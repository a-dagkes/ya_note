"""Docstring."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestListPage(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Notes Author')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='title',
            author=cls.author,
        )
        cls.another_user = User.objects.create(username='Random User')


    def test_note_in_list_for_another_user(self):
        """Авторизованному пользователю не доступны заметки
        другого пользователя.
        """
        self.client.force_login(self.another_user)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, 0)
        self.assertNotIn(self.note, object_list)


    def test_note_list_for_author(self):
        """Автору доступны все его заметки."""
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, 1)
        self.assertIn(self.note, object_list)


class TestNotePage(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Notes Author')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='title',
            author=cls.author,
        )

    def test_authorized_client_form_pages(self):
        """Авторизованному пользователю доступна форма для отправки заметки."""
        self.client.force_login(self.author)
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)

    def test_authorized_client_no_form_pages(self):
        """Форма для отправки заметки отсутствует на страницах
        детального просмотра и удаления заметки.
        """
        self.client.force_login(self.author)
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertNotIn('form', response.context)

    def test_authorized_client_data_pages(self):
        """Отдельная заметка передается на страницу детального просмотра,
        редактирования и удаления заметки в списке объектов object_list
        в словаре context.
        """
        self.client.force_login(self.author)
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('note', response.context)
                note = response.context['note']
                self.assertEqual(note, self.note)
