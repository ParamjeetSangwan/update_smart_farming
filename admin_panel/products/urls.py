# products/urls.py
from django.urls import path
from .admin_views import product_list_view, product_detail_view

urlpatterns = [
    path('', product_list_view, name='admin_product_list'),
    path('<int:product_id>/', product_detail_view, name='admin_product_detail'),
]
