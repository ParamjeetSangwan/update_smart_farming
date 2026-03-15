# admin_panel/middleware/activity_logging.py
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger('admin_activity')

class ActivityLoggingMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            logger.info(f"Admin {request.user.username} accessed {request.path} via {request.method}")
        return None
