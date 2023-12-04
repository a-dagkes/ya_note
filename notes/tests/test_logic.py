from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Notes Author')
        cls.url = reverse('notes:add', None)
        cls.successful_url = reverse('notes:success', None)
        cls.form_data = {
            'title': 'Title',
            'text': 'Text',
            'slug': 'slug',
        }

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_comment(self):
        """Авторизованный пользователь может создать заметку."""
        self.client.force_login(self.author)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.successful_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_auto_slug_generation(self):
        """Поле slug формируется автоматически с помощью slugify,
        если при создании заметки поле не заполнено.
        """
        self.client.force_login(self.author)
        self.form_data.pop('slug', None)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.successful_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, slugify(self.form_data['title']))
        self.assertEqual(note.author, self.author)


class TestExistedNote(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Notes Author')
        cls.random_user = User.objects.create(username='Random User')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='slug',
            author=cls.author,
        )
        cls.form_data = {
            'title': 'Title',
            'text': 'New text',
            'slug': 'someslug',
        }
        cls.successful_url = reverse('notes:success', None)
        cls.auth_client = Client()

    def test_user_cant_use_unoriginal_slug(self):
        """Невозможно создать заметку с неоригинальным полем slug."""
        self.auth_client.force_login(self.author)
        url = reverse('notes:add', None)
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.form_data['slug'] + WARNING),
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_delete_note(self):
        """Автор может удалять свои заметки."""
        self.auth_client.force_login(self.author)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.delete(url)
        self.assertRedirects(response, self.successful_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_author_can_edit_note(self):
        """Автор может редактировать свои заметки."""
        self.auth_client.force_login(self.author)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.post(
            url,
            data=self.form_data,
        )
        self.assertRedirects(response, self.successful_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.slug, self.form_data['slug'])
        self.assertEqual(self.note.author, self.author)

    def test_user_cant_delete_note_of_another_user(self):
        """Авторизованный пользователь не может удалять заметки
        другого пользователя.
        """
        self.auth_client.force_login(self.random_user)
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
    
    def test_user_cant_edit_note_of_another_user(self):
        """Авторизованный пользователь не может редактировать заметки
        другого пользователя.
        """
        original_note_text = self.note.text
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.auth_client.post(url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, original_note_text)
