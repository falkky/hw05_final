from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Comment, Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testauthor')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user)

    def test_urls_authorized_client_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        для авторизованного пользователя.
        """
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTest.user}/': 'posts/profile.html',
            f'/posts/{PostURLTest.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_post_url_for_author_client(self):
        """Страница /posts/{PostURLTest.post.pk}/edit/
        доступна автору поста.
        """
        response = self.author_client.get(
            f'/posts/{PostURLTest.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_for_guest_client(self):
        """URL-адрес использует соответствующий шаблон для
        гостевого пользователя.
        """
        templates_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTest.user}/': HTTPStatus.OK,
            f'/posts/{PostURLTest.post.pk}/': HTTPStatus.OK,
            '/create/': HTTPStatus.FOUND,
            f'/posts/{PostURLTest.post.pk}/edit/': HTTPStatus.FOUND,
        }
        for address, status_code in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_create_redirect_for_guest_client(self):
        """Редирект при открытии /create/ для гостевого пользователя."""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_unexisting_page(self):
        """URL-адрес несуществующей страницы использует соответствующий
        шаблон для всех пользователей.
        """
        templates_url_names = {
            self.author_client: HTTPStatus.NOT_FOUND,
            self.authorized_client: HTTPStatus.NOT_FOUND,
            self.guest_client: HTTPStatus.NOT_FOUND,
        }
        for user, status_code in templates_url_names.items():
            with self.subTest(user=user):
                response = user.get('/unexisting.page/')
                self.assertEqual(response.status_code, status_code)

    def test_custom_template_unexisting_page(self):
        """Проверяем, что что страница 404 отдает кастомный шаблон"""
        response = self.authorized_client.get('/unexisting.page/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template, 'Шаблон-то не кастомный!')
