# orders/urls.py
from django.urls import path
from .admin_views import order_list_view, order_detail_view

urlpatterns = [
    path('', order_list_view, name='admin_order_list'),
    path('<int:order_id>/', order_detail_view, name='admin_order_detail'),
]
