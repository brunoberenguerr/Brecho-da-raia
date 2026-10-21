from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Post


def post_list(request):
    post_list = Post.objects.all()
    return render(request, 'blog/post_list.html', {'post_list': post_list})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})


def post_create(request):
    if request.method == 'POST':
        post = Post.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
        )
        return HttpResponseRedirect(reverse('blog:post_detail', args=[post.pk]))
    return render(request, 'blog/post_form.html')


def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.title = request.POST['title']
        post.content = request.POST['content']
        post.save()
        return HttpResponseRedirect(reverse('blog:post_detail', args=[post.pk]))
    return render(request, 'blog/post_form.html', {'post': post})


def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        return HttpResponseRedirect(reverse('blog:post_list'))
    return render(request, 'blog/post_confirm_delete.html', {'post': post})
