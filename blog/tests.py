from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Post


class PostCrudTests(TestCase):
    def setUp(self):
        self.post = Post.objects.create(title='Óculos Arena', content='<p>Seminovo</p>')

    def test_list(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, 'Óculos Arena')
        self.assertContains(response, reverse('blog:post_detail', args=[self.post.pk]))

    def test_detail_renders_html(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.pk]))
        self.assertContains(response, '<p>Seminovo</p>', html=True)

    def test_detail_404(self):
        response = self.client.get(reverse('blog:post_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_create(self):
        response = self.client.post(reverse('blog:post_create'), {
            'title': 'Palmar Speedo', 'content': '<p>Tam. M</p>',
        })
        post = Post.objects.get(title='Palmar Speedo')
        self.assertRedirects(response, reverse('blog:post_detail', args=[post.pk]))

    def test_create_invalid_shows_errors(self):
        response = self.client.post(reverse('blog:post_create'), {'title': '', 'content': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'errorlist')
        self.assertEqual(Post.objects.count(), 1)

    def test_update(self):
        url = reverse('blog:post_update', args=[self.post.pk])
        self.assertContains(self.client.get(url), 'Óculos Arena')
        self.client.post(url, {'title': 'Óculos Arena Cobra', 'content': '<p>Novo</p>'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Óculos Arena Cobra')

    def test_delete_requires_confirmation(self):
        url = reverse('blog:post_delete', args=[self.post.pk])
        self.assertContains(self.client.get(url), 'Tem certeza')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse('blog:post_list'))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class CommentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('ana', password='senha-de-teste-123')
        self.post = Post.objects.create(title='Pé de pato Arena', content='<p>Tam. 40</p>')
        self.url = reverse('blog:comment_create', args=[self.post.pk])

    def test_detail_links_to_comment_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.pk]))
        self.assertContains(response, self.url)

    def test_comment_requires_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_create_comment_uses_logged_user(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(self.url), 'Pé de pato Arena')
        response = self.client.post(self.url, {'text': 'Ainda disponível?'})
        self.assertRedirects(
            response, reverse('blog:post_detail', args=[self.post.pk]) + '#comentarios',
        )
        comment = Comment.objects.get()
        self.assertEqual((comment.author, comment.post), (self.user, self.post))

    def test_comment_on_missing_post_404(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('blog:comment_create', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_comments_newest_first(self):
        now = timezone.now()
        Comment.objects.create(post=self.post, author=self.user, text='primeiro',
                               posted_at=now - timedelta(hours=1))
        Comment.objects.create(post=self.post, author=self.user, text='segundo', posted_at=now)
        response = self.client.get(reverse('blog:post_detail', args=[self.post.pk]))
        content = response.content.decode()
        self.assertLess(content.index('segundo'), content.index('primeiro'))


class CategoryTests(TestCase):
    def setUp(self):
        self.oculos = Category.objects.create(name='Óculos', description='Óculos de natação')
        self.palmar = Category.objects.create(name='Palmar', description='Palmares de treino')
        self.post = Post.objects.create(title='Óculos Speedo', content='<p>Lente fumê</p>')
        self.post.categories.add(self.oculos)
        self.other = Post.objects.create(title='Palmar Finis', content='<p>Tam. M</p>')
        self.other.categories.add(self.palmar)

    def test_category_list(self):
        response = self.client.get(reverse('blog:category_list'))
        self.assertContains(response, reverse('blog:category_detail', args=[self.oculos.pk]))
        self.assertContains(response, 'Palmares de treino')

    def test_category_detail_lists_only_its_posts(self):
        response = self.client.get(reverse('blog:category_detail', args=[self.oculos.pk]))
        self.assertTemplateUsed(response, 'blog/post_list.html')
        self.assertContains(response, 'Categoria: Óculos')
        self.assertContains(response, 'Óculos Speedo')
        self.assertNotContains(response, 'Palmar Finis')

    def test_category_detail_404(self):
        response = self.client.get(reverse('blog:category_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_post_detail_links_categories(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.pk]))
        self.assertContains(response, reverse('blog:category_detail', args=[self.oculos.pk]))

    def test_header_links_category_list(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertContains(response, reverse('blog:category_list'))
