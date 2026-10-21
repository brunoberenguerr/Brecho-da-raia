from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Case, IntegerField, Value, When

from .formatting import html_to_text, text_to_html
from .models import OTHER_CATEGORY_NAME, Category, Post

MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


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
        fields = ['title', 'price', 'condition', 'size', 'description', 'photo', 'categories',
                  'other_category']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ex.: 150'}),
            'size': forms.TextInput(attrs={'placeholder': 'Ex.: P, M, 40/41, tamanho único'}),
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'categories': forms.CheckboxSelectMultiple,
            'other_category': forms.TextInput(attrs={'placeholder': 'Ex.: touca, snorkel, pull buoy'}),
        }
        labels = {
            'size': 'Tamanho (opcional)',
            'other_category': 'Qual outra categoria?',
        }
        help_texts = {
            'photo': 'Opcional. JPG, PNG, GIF ou WEBP de até 5 MB.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No banco são opcionais por causa dos anúncios antigos; todo anúncio novo deve tê-los
        self.fields['price'].required = True
        self.fields['condition'].required = True
        self.fields['condition'].choices = [('', 'Selecione...')] + Post.CONDITION_CHOICES
        if self.instance.pk:
            self.initial.setdefault('description', html_to_text(self.instance.content))
        # "Outro" sempre por último na lista de categorias
        self.fields['categories'].queryset = Category.objects.order_by(
            Case(When(name=OTHER_CATEGORY_NAME, then=Value(1)), default=Value(0),
                 output_field=IntegerField()),
            'name',
        )
        self.other = Category.objects.filter(name=OTHER_CATEGORY_NAME).first()

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > MAX_PHOTO_SIZE:
            raise forms.ValidationError('A foto deve ter no máximo 5 MB.')
        return photo

    def clean(self):
        cleaned = super().clean()
        categories = list(cleaned.get('categories') or [])
        other_text = cleaned.get('other_category', '').strip()
        if self.other:
            if other_text and self.other not in categories:
                # escreveu qual é a outra categoria: marca "Outro" automaticamente
                categories.append(self.other)
            if self.other in categories and not other_text:
                self.add_error('other_category', 'Diga qual é a outra categoria.')
            if self.other not in categories:
                other_text = ''
        cleaned['categories'] = categories
        cleaned['other_category'] = other_text
        return cleaned

    def save(self, commit=True):
        self.instance.content = text_to_html(self.cleaned_data['description'])
        return super().save(commit)


class SignUpForm(UserCreationForm):
    """Cadastro de usuário: o nome é o que aparece nos anúncios e comentários."""

    first_name = forms.CharField(label='Nome', max_length=150)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {'last_name': 'Sobrenome', 'email': 'E-mail (opcional)'}
