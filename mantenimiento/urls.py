from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('preventivoapp.urls')),
]

# Servir archivos media en producción
if not settings.DEBUG:
    urlpatterns += [
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    ]
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
