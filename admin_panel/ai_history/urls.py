# ai_history/urls.py
from django.urls import path
from .admin_views import ai_history_view

urlpatterns = [
    path('', ai_history_view, name='admin_ai_history'),
]
