"""Docstring."""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm, WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Notes Author')
        cls.url = reverse('notes:add', None)
        cls.successful_url = reverse('notes:success', None)
        # cls.auth_client = Client()
        cls.form_data = {
            'title': 'Title',
            'text': 'Text',
            'slug': 'slug'
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_comment(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, self.successful_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

class TestExistedNote(TestCase):
    UPD_TEXT = 'New text'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Notes Author')
        cls.note = Note.objects.create(
            title='Title',
            text='Text',
            slug='slug',
            author=cls.author,
        )
        cls.successful_url = reverse('notes:success', None)
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)

    def test_user_cant_use_unoriginal_slug(self):
        url = reverse('notes:add', None)
        form_data = {
            'title': self.note.title,
            'text': self.note.text,
            'slug': self.note.slug,
        }
        response = self.auth_client.post(url, data=form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=f'{self.note.slug}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,)) 
        response = self.auth_client.delete(url)
        self.assertRedirects(response, self.successful_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        form_data = {
            'title': self.note.title,
            'text': self.UPD_TEXT,
            'slug': self.note.slug,
        }
        response = self.auth_client.post(url, data=form_data)
        self.assertRedirects(response, self.successful_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.UPD_TEXT)

class TestExistedNoteForbidness(TestCase):
    ORIG_NOTE_TEXT = 'Text'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Notes Author')
        cls.random_user = User.objects.create(username='Random User')
        cls.note = Note.objects.create(
            title='Title',
            text=cls.ORIG_NOTE_TEXT,
            slug='slug',
            author=cls.author,
        )
        cls.successful_url = reverse('notes:success', None)
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.random_user)

    def test_user_cant_delete_note_of_another_user(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client.delete(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_user_cant_edit_note_of_another_user(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        form_data = {
            'title': self.note.title,
            'text': 'new_text',
            'slug': self.note.slug,
        }
        response = self.auth_client.post(url, data=form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.ORIG_NOTE_TEXT)

'''
class TestCommentCreation(TestCase):
    # Текст комментария понадобится в нескольких местах кода, 
    # поэтому запишем его в атрибуты класса.
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        # Адрес страницы с новостью.
        cls.url = reverse('news:detail', args=(cls.news.id,))
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании комментария.
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.     
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        comments_count = Comment.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(comments_count, 0)

    def test_user_can_create_comment(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл к разделу с комментами.
        self.assertRedirects(response, f'{self.url}#comments')
        # Считаем количество комментариев.
        comments_count = Comment.objects.count()
        # Убеждаемся, что есть один комментарий.
        self.assertEqual(comments_count, 1)
        # Получаем объект комментария из базы.
        comment = Comment.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        # Формируем данные для отправки формы; текст включает
        # первое слово из списка стоп-слов.
        bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=bad_words_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
        # Дополнительно убедимся, что комментарий не был создан.
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)


class TestCommentEditDelete(TestCase):
    COMMENT_TEXT = 'Текст комментария'
    NEW_COMMENT_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(title='Заголовок', text='Текст')
        news_url = reverse('news:detail', args=(cls.news.id,))
        cls.url_to_comments = news_url + '#comments'
        cls.author = User.objects.create(username='Автор комментария')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))  
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_comments)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_comment(self):
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария.
        self.comment.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.comment.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
'''