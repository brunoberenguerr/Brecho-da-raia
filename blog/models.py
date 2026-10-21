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
