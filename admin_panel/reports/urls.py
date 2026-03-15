# reports/urls.py
from django.urls import path
from .views import sales_report_view, user_report_view, inventory_report_view

urlpatterns = [
    path('sales/', sales_report_view, name='admin_sales_report'),
    path('users/', user_report_view, name='admin_user_report'),
    path('inventory/', inventory_report_view, name='admin_inventory_report'),
]
