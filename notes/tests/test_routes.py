"""Docstring."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.random_person = User.objects.create(username='Random Person')
        cls.author = User.objects.create(username='Notes Author')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='title',
            author=cls.author,
        )

    def test_common_pages_availability(self):
        """Анонимному пользователю доступны: главная страница, страницы
        регистрации пользователей, входа в учётную запись и выхода из нее.
        """
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        status = HTTPStatus.OK
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_pages_availability_for_author(self):
        """Автору заметки доступны страница просмотра заметки,
        страницы ее редактирования и удаления. Авторизованному пользователю
        не доступны страницы просмотра, редактирования и удаления
        чужих заметок.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.random_person, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_auth_user(self):
        """Авторизованному пользователю доступны страница со списком
        всех своих заметок, страница добавления новой заметки и страница
        успешного добавления заметки.
        """
        user = self.random_person
        self.client.force_login(user)
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
        )
        status = HTTPStatus.OK
        for name, args in urls:
            with self.subTest(user=user, name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """Анонимному пользователю не доступны страницы списка заметок,
        детального просмотра, добавления, редактирования и удаления заметки,
        а также страница успешного добавления заметки.
        При попытке доступа к ним, он перенаправляется на страницу авторизации.
        """
        login_url = reverse('users:login')
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
