from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from recipes.admin_custom import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path("api/", include("api.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
