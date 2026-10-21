from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import PostForm
from .models import Category, Comment, Post


class PostListView(ListView):
    model = Post


class PostDetailView(DetailView):
    model = Post


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm


class PostDeleteView(DeleteView):
    model = Post
    success_url = reverse_lazy('blog:post_list')


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']

    def get_post(self):
        return get_object_or_404(Post, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_post()
        return context

    def form_valid(self, form):
        form.instance.post = self.get_post()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.kwargs['pk']]) + '#comentarios'


class CategoryListView(ListView):
    queryset = Category.objects.annotate(num_posts=Count('posts'))


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'blog/post_list.html'  # reutiliza o template de listagem de posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.object.posts.all()
        return context
