# my_eshop_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include the eshop app's URLs
    path('', include('eshop.urls')),
    path('order-management/', views.order_management_view, name='order_management'),
    path('admin/', admin_site.urls),
]

# Serve media in development if needed
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
