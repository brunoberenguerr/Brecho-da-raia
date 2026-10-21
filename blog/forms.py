from django import forms

from .formatting import html_to_text, text_to_html
from .models import Post


class PostForm(forms.ModelForm):
    # O usuário escreve texto simples; o conteúdo continua guardado como HTML em Post.content
    description = forms.CharField(
        label='Descrição',
        widget=forms.Textarea(attrs={'rows': 14}),
        help_text='Escreva normalmente. Deixe uma linha em branco para começar outro parágrafo, '
                  'comece a linha com "- " para fazer uma lista e cole o link de uma imagem '
                  '(.jpg, .png, .gif ou .webp) sozinho numa linha para exibi-la.',
    )

    class Meta:
        model = Post
        fields = ['title', 'description', 'categories']
        widgets = {
            'categories': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial.setdefault('description', html_to_text(self.instance.content))

    def save(self, commit=True):
        self.instance.content = text_to_html(self.cleaned_data['description'])
        return super().save(commit)
