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
        Note.objects.bulk_create(
            Note(
                title='Title',
                text='Text',
                slug=f'title{index}',
                author=cls.author,
            )
            for index in range(3)
        )

    def test_list_obj(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:list'))
        object_list = response.context['object_list']
        notes_count = len(object_list)
        self.assertEqual(notes_count, 3)

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
