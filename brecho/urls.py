from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from blog.views import SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/cadastro/', SignUpView.as_view(), name='signup'),
    path('contas/', include('django.contrib.auth.urls')),
    path('', include('blog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Em produção (Render) o próprio Django serve os arquivos estáticos coletados e as fotos enviadas
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
