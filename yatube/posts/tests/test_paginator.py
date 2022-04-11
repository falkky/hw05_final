from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorTests(TestCase):
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
            group=cls.group,
        )

        for i in range(0, 12):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group,
            )

    def setUp(self):
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PaginatorTests.user)

    def test_first_page_contains_three_records(self):
        """Проверяем паджинатор на первой странице"""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[f'{PaginatorTests.group.slug}']),
            reverse('posts:profile', args=[f'{PaginatorTests.user}'])
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                posts = response.context.get('page_obj').object_list
                self.assertEqual(len(posts), 10)

    def test_second_page_contains_three_records(self):
        """Проверяем паджинатор на второй странице group_list и profile"""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[f'{PaginatorTests.group.slug}']),
            reverse('posts:profile', args=[f'{PaginatorTests.user}'])
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')), 3)
