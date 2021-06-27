from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import redirect_to_main_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_main_page),
    path('', include('bookapp.urls')),
    path('test/', include('tests.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
