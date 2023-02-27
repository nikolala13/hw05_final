from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User
from yatube.settings import PAGINATION

SLUG = 'test-slug2'
SLUG2 = 'backend'
USERNAME = 'nikolala'
TEXT = 'Тестовый пост '
TITLE = 'Тестовая группа'
DESCRIPTION = 'Тестовое описание'

PAGE_CONTEXT = 'page_obj'

INDEX_URL = reverse('posts:index')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
GROUP2_URL = reverse('posts:group_list', args=[SLUG2])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
CREATE_URL = reverse('posts:post_create')
UNEXIST_URL = '/unexisting_page/'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.all().delete()
        cls.guest = Client()
        cls.author = User.objects.create_user(username=USERNAME)
        cls.another = Client()
        cls.another.force_login(cls.author)

        cls.group2 = Group.objects.create(title='Птички',
                                          slug=SLUG2,
                                          description='блог о птичках')

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

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        urls_checks = (
            (INDEX_URL, PAGE_CONTEXT),
            (GROUP_URL, PAGE_CONTEXT),
            (PROFILE_URL, PAGE_CONTEXT),
            (self.DETAIL_URL, 'post'),
        )
        for url, context in urls_checks:
            with self.subTest():
                response = self.another.get(url).context
                if context == PAGE_CONTEXT:
                    self.assertEqual(len(response[context]), 1)
                    post = response[context][0]
                else:
                    post = response[context]
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)

    def test_page_profile_show_correct_context(self):
        self.assertEqual(
            self.another.get(PROFILE_URL).context['author'], self.post.author
        )

    def test_page_group_show_correct_context(self):
        group = self.another.get(GROUP_URL).context['group']
        self.assertEqual(group, self.post.group)
        self.assertEqual(group.title, self.post.group.title)
        self.assertEqual(group.slug, self.post.group.slug)
        self.assertEqual(group.description, self.post.group.description)

    def test_pagination(self):
        """Тестируем пагинацию в шаблонах index, group_list & profile"""
        Post.objects.bulk_create(
            Post(author=self.author,
                 text=f'Пост номер {i}',
                 group=self.group2)
            for i in range(3, PAGINATION + PAGINATION // 2)
        )

        prefix = '?page=2'
        pages_and_counts = [
            [INDEX_URL + prefix, 3],
            [GROUP_URL + prefix, 1],
            [PROFILE_URL + prefix, 3],
        ]

        for url, count in pages_and_counts:
            with self.subTest(url=url):
                self.assertEqual(len(self.another.get(url)
                                     .context[PAGE_CONTEXT]), count)

    def test_additional_check_with_post_creation(self):
        """Пост не попал на чужую для него групп-ленту"""
        self.assertNotIn(
            self.post, self.another.get(GROUP2_URL).context[PAGE_CONTEXT])