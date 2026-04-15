"""
URL configuration for yunnan_backend project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls_auth')),
    path('api/users/', include('apps.users.urls')),
    path('api/', include('apps.sales.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/predictions/', include('apps.predictions.urls')),
]
