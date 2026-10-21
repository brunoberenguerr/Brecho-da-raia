from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Post(models.Model):
    """Anúncio de um item de natação usado."""

    title = models.CharField('título', max_length=200)
    content = models.TextField('conteúdo (HTML)')
    posted_at = models.DateTimeField('data de postagem', default=timezone.now)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.pk])


class Comment(models.Model):
    """Pergunta ou proposta de um usuário em um anúncio."""

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments', verbose_name='post',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='autor',
    )
    text = models.TextField('texto')
    posted_at = models.DateTimeField('data de postagem', default=timezone.now)

    class Meta:
        ordering = ['-posted_at']
        verbose_name = 'comentário'

    def __str__(self):
        return f'{self.author} em "{self.post}"'
