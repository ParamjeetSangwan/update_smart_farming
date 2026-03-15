# admin_panel/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='admin_dashboard'),
    path('activity/', views.admin_activity_view, name='admin_activity'),

    # Users
    path('users/', views.admin_users_view, name='admin_users'),
    path('users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
    path('users/<int:user_id>/toggle/', views.admin_user_toggle_active, name='admin_user_toggle'),
    path('users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('users/<int:user_id>/staff/', views.admin_user_make_staff, name='admin_user_staff'),
    path('users/<int:user_id>/block/', views.admin_user_block, name='admin_user_block'),
    path('users/<int:user_id>/unblock/', views.admin_user_unblock, name='admin_user_unblock'),
    path('users/<int:user_id>/2fa/', views.admin_user_toggle_2fa, name='admin_user_2fa'),

    # Products
    path('products/', views.admin_products_view, name='admin_products'),
    path('products/add/', views.admin_product_add_view, name='admin_product_add'),
    path('products/tool/<int:tool_id>/edit/', views.admin_tool_edit_view, name='admin_tool_edit'),
    path('products/tool/<int:tool_id>/delete/', views.admin_tool_delete_view, name='admin_tool_delete'),
    path('products/pesticide/<int:pesticide_id>/edit/', views.admin_pesticide_edit_view, name='admin_pesticide_edit'),
    path('products/pesticide/<int:pesticide_id>/delete/', views.admin_pesticide_delete_view, name='admin_pesticide_delete'),

    # Orders
    path('orders/', views.admin_orders_view, name='admin_orders'),
    path('orders/<int:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('orders/<int:order_id>/delete/', views.admin_order_delete_view, name='admin_order_delete'),

    # Crops
    path('crops/', views.admin_crops_view, name='admin_crops'),
    path('crops/add/', views.admin_crop_add_view, name='admin_crop_add'),
    path('crops/<int:crop_id>/edit/', views.admin_crop_edit_view, name='admin_crop_edit'),
    path('crops/<int:crop_id>/delete/', views.admin_crop_delete_view, name='admin_crop_delete'),

    # AI History
    path('ai-history/', views.admin_ai_history_view, name='admin_ai_history'),
    path('ai-history/<int:query_id>/delete/', views.admin_ai_delete_view, name='admin_ai_delete'),

    # Announcements
    path('announcements/', views.admin_announcements_view, name='admin_announcements'),
    path('announcements/create/', views.admin_announcement_create, name='admin_announcement_create'),
    path('announcements/<int:ann_id>/delete/', views.admin_announcement_delete, name='admin_announcement_delete'),

    # Reports & Settings
    path('reports/', views.admin_reports_view, name='admin_reports'),
    path('settings/', views.admin_settings_view, name='admin_settings'),
]