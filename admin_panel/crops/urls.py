# crops/urls.py
from django.urls import path
from .admin_views import crop_list_view

urlpatterns = [
    path('', crop_list_view, name='admin_crop_list'),
]
