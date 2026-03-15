# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path('confirm/', views.confirm_order_view, name='confirm_order'),
    path('my-orders/', views.my_orders_view, name='my_orders'),
]