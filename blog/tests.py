from django.test import TestCase
from django.urls import reverse

from .models import Post


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
