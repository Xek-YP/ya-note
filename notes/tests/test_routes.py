from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_availability_for_comment_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit', 'notes:detail', 'notes:delete'):
                url = reverse(name, args=(self.notes.slug,))
                response = self.client.get(url)
                self.assertEqual(response.status_code, status) 

    def test_pages_availability(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = (
                    self.client.post(url)
                    if name == 'users:logout'
                    else self.client.get(url))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):

        login_url = reverse('users:login')
        for name in (
            'notes:add',
            'notes:edit',
            'notes:detail',
            'notes:delete',
            'notes:list'
            ):
            with self.subTest(name=name):
                url = (reverse(name)
                       if (name == 'notes:add' or name == 'notes:list')
                       else reverse(name, args=(self.notes.slug,)))
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
