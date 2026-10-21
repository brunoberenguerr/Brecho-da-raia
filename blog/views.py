from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from .forms import PostForm, SignUpForm
from .models import Category, Comment, Post


class PostOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Visitantes vão para o login; usuários que não são donos do anúncio recebem 403."""

    def test_func(self):
        return self.get_object().can_edit(self.request.user)


SOLD_LAST = ('is_sold', '-posted_at')  # anúncios vendidos vão para o fim das listagens


class PostListView(ListView):
    queryset = Post.objects.order_by(*SOLD_LAST)


class PostDetailView(DetailView):
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.object.can_edit(self.request.user)
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostOwnerRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm


class PostDeleteView(PostOwnerRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:post_list')


class PostToggleSoldView(PostOwnerRequiredMixin, SingleObjectMixin, View):
    """Marca o anúncio como vendido, ou o reabre se já estava vendido."""

    model = Post
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        post.is_sold = not post.is_sold
        post.save(update_fields=['is_sold'])
        return redirect(post)


class MyPostsView(LoginRequiredMixin, ListView):
    template_name = 'blog/post_list.html'
    extra_context = {'my_posts': True}

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by(*SOLD_LAST)


class SellerDetailView(DetailView):
    model = get_user_model()
    slug_field = 'username'
    slug_url_kwarg = 'username'
    context_object_name = 'seller'  # "user" já é o usuário logado nos templates
    template_name = 'blog/post_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_list'] = self.object.posts.order_by(*SOLD_LAST)
        return context


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
        context['post_list'] = self.object.posts.order_by(*SOLD_LAST)
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('blog:post_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.POST.get('next') or self.request.GET.get('next', '')
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)  # já entra logado depois de criar a conta
        next_url = self.request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()},
                                           require_https=self.request.is_secure()):
            return redirect(next_url)
        return redirect('blog:post_list')
