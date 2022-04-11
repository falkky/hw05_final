import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Comment, Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostPagesTests.user)

    def test_posts_detail_pages_authorized_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        для авторизованного пользователя.
        """
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', args=[f'{PostPagesTests.group.slug}']
            ),
            'posts/profile.html': reverse(
                'posts:profile', args=[f'{PostPagesTests.user}']
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', args=[f'{PostPagesTests.post.pk}']
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_detail_pages_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон
        для автора поста.
        """
        response = self.author_client.get(
            reverse('posts:post_edit', args=[f'{PostPagesTests.post.pk}'])
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_page_show_correct_context(self):
        """Шаблон страницы index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context = {
            first_object.text: PostPagesTests.post.text,
            first_object.group: PostPagesTests.group,
            first_object.pk: PostPagesTests.post.pk,
        }
        for value, expectes in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectes)

    def test_group_list_page_show_correct_context(self):
        """Шаблон страницы group_list сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=[f'{PostPagesTests.group.slug}'])
        )
        context = {
            response.context.get('group').slug: PostPagesTests.group.slug,
            response.context.get('post').group: PostPagesTests.group,
        }
        for value, expectes in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectes)

    def test_profile_page_show_correct_context(self):
        """Шаблон страницы profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:profile', args=[f'{PostPagesTests.user}'])
        )
        first_object = response.context['user_posts'][0]
        context = {
            response.context.get('author'): PostPagesTests.user,
            first_object: PostPagesTests.post,
        }
        for value, expectes in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectes)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон страницы post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', args=[f'{PostPagesTests.post.pk}'])
        )
        context = {
            response.context.get('user'): PostPagesTests.user,
            response.context.get('post'): PostPagesTests.post,
            response.context.get('post').pk: PostPagesTests.post.pk,
        }
        for value, expectes in context.items():
            with self.subTest(value=value):
                self.assertEqual(value, expectes)

    def test_post_create_page_show_correct_context(self):
        """Шаблон страницы post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expectes in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expectes)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон страницы post_edit сформирован с правильным контекстом"""
        response = self.author_client.get(reverse(
            'posts:post_edit', args=[f'{PostPagesTests.post.pk}'])
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expectes in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expectes)

    def test_post_page_show_correct(self):
        """Если при создании поста указать группу, то этот пост появляется
        на главной странице, странице выбранной группы и в профайле.
        """
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[f'{PostPagesTests.group.slug}']),
            reverse('posts:profile', args=[f'{PostPagesTests.user}'])
        ]
        for page in page_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                posts = response.context.get('page_obj').object_list
                self.assertIn(PostPagesTests.post, posts)

    def test_post_has_correct_group_on_profile_and_group_pages(self):
        """Проверяем, что пост не попал в группу,
         для которой не был предназначен
        """
        group_original = PostPagesTests.group
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[f'{PostPagesTests.group.slug}']),
            reverse('posts:profile', args=[f'{PostPagesTests.user}'])
        ]
        for page in page_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                group_expected = response.context.get('page_obj')[0].group
                self.assertEqual(group_original, group_expected)

    def test_page_show_correct_context_image(self):
        """Шаблон страницы сформирован с изображением в контексте"""
        page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[f'{PostPagesTests.group.slug}']),
            reverse('posts:profile', args=[f'{PostPagesTests.user}']),
            reverse('posts:post_detail', args=[f'{PostPagesTests.post.pk}'])
        ]
        for page in page_names:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                if page == reverse(
                                   'posts:post_detail',
                                   args=[f'{PostPagesTests.post.pk}']
                ):
                    image = response.context.get('post').image
                else:
                    image = response.context.get('page_obj')[0].image
                self.assertTrue(image, 'Нет передается изображение')

    def test_add_comment_post_url_for_authorized_client(self):
        """Комментирование поста доступно
        только авторизованному пользователю.
        """
        comment_form = {
            'text': 'Очень остроумный комментарий',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=[f'{PostPagesTests.post.pk}']),
            data=comment_form,
            follow=True
        )
        # Если пользователь не авторизован перенаправляем
        # на страницу авторизации
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostPagesTests.post.pk}/comment/'
        )

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок
        """
        follow_count = Follow.objects.count()
        # Запрос на подписку
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args=[f'{PostPagesTests.user}']
            )
        )
        # Проверяем, что кол-во подписок увеличилось
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        # Запрос на отписку
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                args=[f'{PostPagesTests.user}']
            )
        )
        # Проверяем, что кол-во подписок уменьшилось
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_index_page(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан.
        """
        response_1 = self.authorized_client.get(reverse('posts:follow_index'))
        posts_unfollow = response_1.context.get('page_obj').object_list
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args=[f'{PostPagesTests.user}']
            )
        )
        response_2 = self.authorized_client.get(reverse('posts:follow_index'))
        posts_follow = response_2.context.get('page_obj').object_list
        self.assertNotEqual(
            posts_unfollow,
            posts_follow,
            'Новая запись не появилась'
        )
    
    def test_follow_on_onself(self):
        """Проверяем, что нельзя подписаться на самого себя"""
        # Запрос на подписку
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args=[f'{self.user}']
            )
        )
        # Проверяем, что кол-во подписок уменьшилось
        self.assertEqual(
            response.status_code,
            403,
            'Пользователь может подписаться на самого себя'
        )
