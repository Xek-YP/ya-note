from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()

class TestListNotes(TestCase):
    NOTES_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    def test_list_have_note(self):
        """
        Проверяет есть ли объект note в словаре context,
        у автора и другого пользователя.
        """
        users_have_note = ((self.author, True), (self.reader, False))
        for user, have_note in users_have_note:
            self.client.force_login(user)
            response = self.client.get(self.NOTES_URL)
            object_list = response.context['object_list']
            self.assertEqual(self.notes in object_list, have_note)
    
    def test_pages_contains_form(self):
        """
        Проверяет наличие формы на страницах
        добавления и изменения заметок.
        """
        urls = (('notes:add', None), ('notes:edit', self.notes.slug))
        self.client.force_login(self.author)
        for name, slug in urls:
            with self.subTest(name=name):
                url = reverse(name, args=[slug]) if slug else reverse(name)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
