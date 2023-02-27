import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Comment, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.REVERSE_ADDRESS_PROFILE = reverse(
            'posts:profile', args=(self.user.username,)
        )
        self.REVERSE_ADDRESS_CREATE = reverse(
            'posts:post_create'
        )
        self.REVERSE_ADDRESS_EDIT = reverse(
            'posts:post_edit', args=(self.post.pk,)
        )
        self.REVERSE_ADDRESS_DETAIL = reverse(
            'posts:post_detail', args=(self.post.pk,)
        )
        self.REVERSE_ADRESS_COMMENT = reverse(
            'posts:add_comment', args=(self.post.pk,)
        )
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка создания поста."""
        count_post = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост'
        }
        response = self.authorized_client.post(
            self.REVERSE_ADDRESS_CREATE,
            data=form_data,
        )
        post = Post.objects.last()
        context = {'username': self.user.username}
        self.assertRedirects(response, self.REVERSE_ADDRESS_PROFILE)
        self.assertEqual(Post.objects.count(), count_post + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user, 'Author')

    def test_edit_post(self):
        """Редактирование поста прошло успешно."""
        form_data_new = {
            'text': 'Тестовый пост'
        }
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        self.authorized_client.post(
            self.REVERSE_ADDRESS_EDIT,
            data=form_data_new,
        )

        self.assertEqual(Post.objects.last().text,
                         form_data_new['text'])

    def cheking_context(self, expect_answer):
        """Проверка контекста страниц."""
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                resp_context = obj
                self.assertEqual(resp_context, answer)

    def test_create_post_with_img(self):
        """Создается пост с картинкой."""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
           self.REVERSE_ADDRESS_CREATE,
           data=form_data,
           follow=True
        )
        self.assertRedirects(
            response,
            self.REVERSE_ADDRESS_PROFILE
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.order_by('-pk')[0]
        expect_answer = {
            last_post.text: form_data['text'],
            str(last_post.image): str(last_post.image),
        }
        self.cheking_context(expect_answer)

    def test_create_comment_authorized_user(self):
        """Валидная форма создает комментарий."""
        post = Post.objects.create(
            author=CreateFormTests.user,
            text='Текст',
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            self.REVERSE_ADRESS_COMMENT,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, self.REVERSE_ADDRESS_DETAIL
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        last_comment = Comment.objects.last()
        self.assertEqual(last_comment.text, form_data['text'])
        response = self.authorized_client.get(
            self.REVERSE_ADDRESS_DETAIL
        )

