from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()

class TestCanAddNotes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.author = User.objects.create(username='Автор')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='New-slug',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'Slug'
        }
        cls.url = reverse('notes:add')

    def test_anonymous_user_cant_create_note(self):
        """
        Проверяет, что анонимный пользователь
        не может создать заметку.
        """
        self.client.post(self.url, data=self.form_data)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1)

    def test_user_can_create_post(self):
        """Проверяет, пользователь может создавать заметки."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        note_count = Note.objects.count()
        self.assertEqual(note_count, 2)
        note = Note.objects.last()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])

    def test_not_unique_slug(self):
        """
        Проверяет невозможнсть создания
        двух заметкок с одинаковым slug.
        """
        self.form_data['slug'] = self.notes.slug
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.notes.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """
        Проверяет, что если при создании заметки не заполнен slug,
        то он формируется автоматически
        """
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

class TestEditNote(TestCase):
    NEW_TITLE = 'New Title'
    NEW_TEXT = 'New Text'
    NEW_SLUG = 'New Slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='New-slug',
            author=cls.author
        )
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.url_edit = reverse('notes:edit', args=[cls.notes.slug])
        cls.url_delete = reverse('notes:delete', args=[cls.notes.slug])
        cls.form_data = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'Slug'
        }

    def test_author_can_edit_note(self):
        """Проверяет возможность изменения записи автором"""
        response = self.auth_client.post(self.url_edit, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.title, self.form_data['title'])
        self.assertEqual(self.notes.text, self.form_data['text'])
        self.assertEqual(self.notes.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Проверяет невозможность изменения записи дпугим пользователем."""
        response = self.user_client.post(self.url_edit, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get()
        self.assertEqual(note_from_db.title, self.notes.title)
        self.assertEqual(note_from_db.text, self.notes.text)
        self.assertEqual(note_from_db.slug, self.notes.slug)

    def test_author_can_delete_note(self):
        """Проверяет возможность удаления записи автором."""
        response = self.auth_client.post(self.url_delete)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Проверяет невозможность удаления записи другим пользователем."""
        response = self.user_client.post(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)