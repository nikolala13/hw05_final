from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User, Follow, Comment

USERNAME = 'nikolala'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с длинной имени более 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        with self.subTest(name='Все верно'):
            self.assertEqual(str(self.group), group.title)
            self.assertEqual(str(self.post), post.text[:15])


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.followed = User.objects.create_user(username='followed')
        cls.post = Post.objects.create(
            author=cls.followed,
            text='Тестовый текст'
        )

    def setUp(self):
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.follower)
        self.authorized_client_followed = Client()
        self.authorized_client_followed.force_login(self.followed)

    def test_follow(self):
        """
        Авторизованный пользователь
        может подписываться на других пользователей
        и удалять их из подписок.
        """
        follows_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.followed.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.authorized_client_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.followed.username}
            )
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_post_in_follow_page(self):
        """
        Пост появляется в ленте тех,
        кто на него подписан
        и не появляется в ленте тех,
        кто не подписан."""
        self.authorized_client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.followed.username}
            )
        )
        response_followed = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        self.assertContains(response_followed, self.post.text)
        response_unfollowed = self.authorized_client_followed.get(
            reverse('posts:follow_index'))
        self.assertNotContains(response_unfollowed, self.post.text)


class CommentsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий',
        )

    def setUp(self):
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_unauthorized_user_cant_comment(self):
        """Неавторизованный пользователь не может оставлять комментарии."""

        form_data = {
            'text': self.comment.text,
        }
        response = self.guest.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

    def test_authorized_user_can_comment(self):
        """Комментарий появляется на странице поста."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertContains(response, self.comment.text)
