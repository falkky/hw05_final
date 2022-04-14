import shutil
import tempfile
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_new = Group.objects.create(
            title='Еще одна тестовая группа',
            slug='test-slug-two',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для редактирования',
            group=cls.group,

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
        self.authorized_client = Client()
        self.authorized_client.force_login(FormTest.user)

    def test_create_post(self):
        """Проверка создания поста при отправке валидной формы"""
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Тестовый текст',
            'group': FormTest.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', args=[f'{FormTest.user}'])
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создалась запись с изображением
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.pk,
                image='posts/small.gif',
            ).exists(),
            'Не создалась запись с изображением!'
        )

    def test_create_post_with_empty_image(self):
        """Проверка создания поста если передадим не изображение"""
        # Создаем пустую картинку
        small_gif = (b'')
        empty_image = SimpleUploadedFile(
                name='img_file.gif',
                content=small_gif,
                content_type='image/gif'
            )
        form_data = {
            'text': 'Тестовый текст',
            'group': FormTest.group.pk,
            'image': empty_image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'image',
            'Отправленный файл пуст.'
        )

    def test_edit_post(self):
        """Проверка редактирования поста при отправке валидной формы"""
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[f'{FormTest.post.pk}']),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[f'{FormTest.post.id}'])
        )

    def test_post_has_changed(self):
        """Проверяем изменился ли пост после редактирования"""
        form_data = {
            'text': 'Новый тестовый текст',
            'group': self.group_new.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[f'{FormTest.post.pk}']),
            data=form_data,
            follow=True
        )
        original_post = {
            'original_text': FormTest.post.text,
            'original_group': FormTest.post.group,
        }
        edited_post = {
            'edited_text': response.context.get('post').text,
            'edited_group': response.context.get('post').group,
        }
        for original, edited in original_post.values(), edited_post.values():
            with self.subTest(original=original):
                self.assertNotEqual(original, edited, 'NotChanged!')

    def test_create_comment(self):
        """Проверяем появляется ли комментарий на странице поста"""
        # после успешной отправки комментарий появляется на странице поста.
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Очень остроумный комментарий',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[f'{FormTest.post.pk}']),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTest.user)

    def test_cache_index_page(self):
        """Список постов на главной странице сайта
        хранится в кэше и обновляется раз в 20 секунд
        """
        # Запрашиваем главную страницу
        response_1 = self.authorized_client.get(reverse('posts:index'))
        # Удаляем посты
        Post.objects.all().delete()
        # Снова запрашиваем главную страницу
        response_2 = self.authorized_client.get(reverse('posts:index'))
        # Сравниваем вновь запрошенную страницу с сохраненным контетом
        self.assertEqual(
            response_1.content,
            response_2.content,
            'Кеширование не работает'
        )
        # Очищаем кеш
        cache.clear()
        # Снова запрашиваем главную страницу
        response_3 = self.authorized_client.get(reverse('posts:index'))
        # Сравниваем вновь запрошенную страницу с сохраненным контетом
        self.assertNotEqual(
            response_1.content,
            response_3.content,
            'Кеш не очистился'
        )
