from http import HTTPStatus

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User

SLUG = 'test-slug13'
USERNAME = 'nikolala'
TEXT = 'Тестовый пост'
TITLE = 'Тестовая группа'
DESCRIPTION = 'Тестовое описание'

INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
CREATE_URL = reverse('posts:post_create')
UNEXIST_URL = '/unexisting_page/'
# NOT_CSRF_URL = reverse()
LOGIN_URL = reverse('users:login')
CREATE_REDIRECT_URL = f'{LOGIN_URL}?next={CREATE_URL}'
EDIT_REDIRECT_URL = f'{LOGIN_URL}?next=%2Fposts%2F1%2Fedit%2F'

OK = HTTPStatus.OK
FOUND = HTTPStatus.FOUND
NOT_FOUND = HTTPStatus.NOT_FOUND


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.guest = Client()
        cls.author = User.objects.create_user(username=USERNAME)
        cls.another = Client()
        cls.another.force_login(cls.author)
        cls.not_author = Client()
        cls.user2 = User.objects.create_user(username='Not_author')
        cls.not_author.force_login(cls.user2)

        cls.group = Group.objects.create(
            title=TITLE,
            slug=SLUG,
            description=DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=TEXT,
            group=cls.group,
        )

        cls.DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])

    def setUp(self):
        cache.clear()

    def test_url_exists_at_desired_location(self):
        """Доступ к страницам пользователям"""
        guest = self.guest
        another = self.another
        not_author = self.not_author
        urls_client_status = [
            [INDEX_URL, guest, OK],
            [GROUP_URL, guest, OK],
            [PROFILE_URL, guest, OK],
            [self.DETAIL_URL, guest, OK],
            [self.EDIT_URL, guest, FOUND],
            [self.EDIT_URL, another, OK],
            [self.EDIT_URL, not_author, FOUND],
            [CREATE_URL, guest, FOUND],
            [CREATE_URL, another, OK],
            [UNEXIST_URL, guest, NOT_FOUND],
        ]

        for url, client, code in urls_client_status:
            with self.subTest(url=url, client=client, code=code):
                self.assertEqual(client.get(url).status_code, code)

    def test_redirect(self):
        """Пользователи переадресуются на нужные страницы."""
        pages_client_redirect = (
            (self.EDIT_URL, self.not_author, EDIT_REDIRECT_URL),
            (CREATE_URL, self.guest, CREATE_REDIRECT_URL),
            (self.EDIT_URL, self.guest, EDIT_REDIRECT_URL),
        )
        for url, client, adress in pages_client_redirect:
            with self.subTest(url=url, client=client, adress=adress):
                self.assertRedirects(self.client.get(url), adress)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.DETAIL_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/post_create.html',
            self.EDIT_URL: 'posts/post_create.html',
            UNEXIST_URL: 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(self.another.get(address), template)
