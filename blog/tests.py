import io
import shutil
import tempfile
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .formatting import html_to_text, text_to_html
from .forms import PostForm
from .models import Category, Comment, Post


class PostCrudTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('vendedor')
        self.post = Post.objects.create(title='Óculos Arena', content='<p>Seminovo</p>',
                                        author=self.owner)
        self.client.force_login(self.owner)

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
            'title': 'Palmar Speedo', 'description': 'Tamanho M.\nPouco uso.\n\n- Tiras novas',
        })
        post = Post.objects.get(title='Palmar Speedo')
        self.assertRedirects(response, reverse('blog:post_detail', args=[post.pk]))
        self.assertEqual(post.author, self.owner)
        self.assertEqual(post.content, '<p>Tamanho M.<br>Pouco uso.</p>\n<ul><li>Tiras novas</li></ul>')

    def test_create_escapes_typed_html(self):
        self.client.post(reverse('blog:post_create'), {
            'title': 'Touca', 'description': '<script>alert(1)</script>',
        })
        post = Post.objects.get(title='Touca')
        self.assertEqual(post.content, '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>')

    def test_create_invalid_shows_errors(self):
        response = self.client.post(reverse('blog:post_create'), {'title': '', 'description': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'errorlist')
        self.assertEqual(Post.objects.count(), 1)

    def test_update(self):
        url = reverse('blog:post_update', args=[self.post.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Óculos Arena')
        # o HTML salvo volta como texto simples no formulário
        self.assertContains(response, 'Seminovo</textarea>')
        self.client.post(url, {'title': 'Óculos Arena Cobra', 'description': 'Novo'})
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Óculos Arena Cobra')
        self.assertEqual(self.post.content, '<p>Novo</p>')

    def test_delete_requires_confirmation(self):
        url = reverse('blog:post_delete', args=[self.post.pk])
        self.assertContains(self.client.get(url), 'Tem certeza')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, reverse('blog:post_list'))
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class PostPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('dono')
        self.other = User.objects.create_user('outro')
        self.staff = User.objects.create_user('equipe',
                                              is_staff=True)
        self.post = Post.objects.create(title='Traje Arena', content='<p>Tam. 22</p>',
                                        author=self.owner)
        self.detail = reverse('blog:post_detail', args=[self.post.pk])
        self.update = reverse('blog:post_update', args=[self.post.pk])
        self.delete = reverse('blog:post_delete', args=[self.post.pk])

    def test_visitor_does_not_see_buttons_and_is_sent_to_login(self):
        self.assertNotContains(self.client.get(self.detail), self.update)
        for url in (reverse('blog:post_create'), self.update, self.delete):
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_visitor_cannot_delete_with_post(self):
        self.client.post(self.delete)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_other_user_gets_403(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.detail), self.update)
        response = self.client.get(self.update)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Acesso negado', status_code=403)
        self.assertEqual(self.client.post(self.delete).status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_owner_sees_buttons(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.detail)
        self.assertContains(response, self.update)
        self.assertContains(response, self.delete)

    def test_staff_can_edit_any_post(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.update).status_code, 200)
        self.client.post(self.delete)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())


class CommentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('ana')
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


class FormattingTests(TestCase):
    TEXT = ('Traje usado em duas provas.\nTecido firme.\n\n'
            '- Tamanho: 20\n- Estado: muito bom\n\n'
            'https://i.imgur.com/abc123.jpg\n\n'
            'Preço: R$ 850,00')

    def test_text_to_html(self):
        self.assertEqual(text_to_html(self.TEXT), (
            '<p>Traje usado em duas provas.<br>Tecido firme.</p>\n'
            '<ul><li>Tamanho: 20</li><li>Estado: muito bom</li></ul>\n'
            '<p><img src="https://i.imgur.com/abc123.jpg" alt=""></p>\n'
            '<p>Preço: R$ 850,00</p>'
        ))

    def test_round_trip(self):
        self.assertEqual(html_to_text(text_to_html(self.TEXT)), self.TEXT)

    def test_only_image_links_become_images(self):
        self.assertNotIn('<img', text_to_html('https://exemplo.com/pagina'))
        self.assertNotIn('<img', text_to_html('javascript:alert(1).png'))

    def test_legacy_html_becomes_readable_text(self):
        html = '<p>Kit <em>completo</em>.</p><table><tr><td>Palmar</td><td>M</td></tr></table>'
        self.assertEqual(html_to_text(html), 'Kit completo.\n\nPalmar: M')


def png_upload(name='foto.png', size=(40, 30)):
    buffer = io.BytesIO()
    Image.new('RGB', size, (11, 92, 143)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class PhotoUploadTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        self.override = override_settings(MEDIA_ROOT=self.media)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.user = get_user_model().objects.create_user('vendedor')
        self.client.force_login(self.user)

    def create(self, **extra):
        data = {'title': 'Pé de pato', 'description': 'Tam. 40', **extra}
        return self.client.post(reverse('blog:post_create'), data)

    def test_upload_photo_shows_on_detail_and_list(self):
        self.create(photo=png_upload())
        post = Post.objects.get()
        self.assertTrue(post.photo.name.startswith('anuncios/'))
        self.assertContains(self.client.get(post.get_absolute_url()), post.photo.url)
        self.assertContains(self.client.get(reverse('blog:post_list')), post.photo.url)

    def test_photo_is_optional(self):
        self.create()
        self.assertFalse(Post.objects.get().photo)

    def test_rejects_file_that_is_not_an_image(self):
        fake = SimpleUploadedFile('foto.png', b'<script>alert(1)</script>', content_type='image/png')
        response = self.create(photo=fake)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Post.objects.exists())

    def test_rejects_photo_over_size_limit(self):
        with mock.patch('blog.forms.MAX_PHOTO_SIZE', 10):
            response = self.create(photo=png_upload())
        self.assertContains(response, 'no máximo 5 MB')
        self.assertFalse(Post.objects.exists())


class OtherCategoryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('vendedor')
        self.client.force_login(self.user)
        self.other = Category.objects.get(name='Outro')  # criada pela migração 0006
        self.trajes = Category.objects.create(name='Trajes', description='Trajes')

    def create(self, **extra):
        data = {'title': 'Touca Arena', 'description': 'Silicone', **extra}
        return self.client.post(reverse('blog:post_create'), data)

    def test_other_is_listed_last_in_form(self):
        names = [category.name for category in PostForm().fields['categories'].queryset]
        self.assertEqual(names, ['Trajes', 'Outro'])

    def test_other_requires_description(self):
        response = self.create(categories=[self.other.pk])
        self.assertContains(response, 'Diga qual é a outra categoria.')
        self.assertFalse(Post.objects.exists())

    def test_other_with_description(self):
        self.create(categories=[self.other.pk], other_category='Touca')
        post = Post.objects.get()
        self.assertEqual(list(post.categories.all()), [self.other])
        self.assertEqual(post.other_category, 'Touca')
        self.assertContains(self.client.get(post.get_absolute_url()), 'Outro: Touca')

    def test_typing_other_category_checks_other_automatically(self):
        self.create(categories=[self.trajes.pk], other_category='Touca')
        post = Post.objects.get()
        self.assertEqual(set(post.categories.all()), {self.trajes, self.other})

    def test_unchecking_other_clears_description(self):
        self.create(categories=[self.other.pk], other_category='Touca')
        post = Post.objects.get()
        self.client.post(reverse('blog:post_update', args=[post.pk]), {
            'title': post.title, 'description': 'Silicone', 'categories': [self.trajes.pk],
        })
        post.refresh_from_db()
        self.assertEqual(post.other_category, '')
        self.assertEqual(list(post.categories.all()), [self.trajes])


class SignUpTests(TestCase):
    PASSWORD = 'Raia#natacao2026'

    def data(self, **extra):
        return {'username': 'marina', 'first_name': 'Marina', 'last_name': 'Costa',
                'email': '', 'password1': self.PASSWORD, 'password2': self.PASSWORD, **extra}

    def test_header_and_login_page_link_to_signup(self):
        self.assertContains(self.client.get(reverse('blog:post_list')), reverse('signup'))
        self.assertContains(self.client.get(reverse('login')), reverse('signup'))

    def test_signup_creates_regular_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), self.data())
        self.assertRedirects(response, reverse('blog:post_list'))
        user = get_user_model().objects.get(username='marina')
        self.assertEqual(user.get_full_name(), 'Marina Costa')
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password(self.PASSWORD))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signup_returns_to_next(self):
        post = Post.objects.create(title='Óculos', content='<p>x</p>')
        target = reverse('blog:comment_create', args=[post.pk])
        response = self.client.post(reverse('signup'), self.data(next=target))
        self.assertRedirects(response, target)

    def test_signup_ignores_external_next(self):
        response = self.client.post(reverse('signup'), self.data(next='https://malicioso.com/'))
        self.assertRedirects(response, reverse('blog:post_list'))

    def test_name_is_required(self):
        response = self.client.post(reverse('signup'), self.data(first_name=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())

    def test_password_confirmation_must_match(self):
        response = self.client.post(reverse('signup'), self.data(password2='Outra#senha2026'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())

    def test_weak_password_is_rejected(self):
        response = self.client.post(reverse('signup'), self.data(password1='123', password2='123'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())

    def test_duplicate_username_is_rejected(self):
        get_user_model().objects.create_user('marina')
        response = self.client.post(reverse('signup'), self.data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_logged_user_is_redirected_away(self):
        self.client.force_login(get_user_model().objects.create_user('ana'))
        self.assertRedirects(self.client.get(reverse('signup')), reverse('blog:post_list'))
