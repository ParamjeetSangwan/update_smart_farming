# users/urls.py
from django.urls import path
from .admin_views import user_list_view, user_detail_view

urlpatterns = [
    path('', user_list_view, name='admin_user_list'),
    path('<int:user_id>/', user_detail_view, name='admin_user_detail'),
]
