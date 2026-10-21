from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 14}),
        }
        help_texts = {
            'content': 'Aceita HTML: use <p>, <ul>, <table>, <img src="..."> etc.',
        }
