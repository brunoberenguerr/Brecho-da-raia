from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('anuncios/novo/', views.PostCreateView.as_view(), name='post_create'),
    path('anuncios/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('anuncios/<int:pk>/editar/', views.PostUpdateView.as_view(), name='post_update'),
    path('anuncios/<int:pk>/remover/', views.PostDeleteView.as_view(), name='post_delete'),
]
