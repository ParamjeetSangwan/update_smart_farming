# settings/views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def settings_view(request):
    # Placeholder settings data
    site_settings = {
        'site_name': 'SmartFarming',
        'logo_url': '/static/images/logo.png',
        'contact_email': 'support@smartfarming.com',
        'support_phone': '+91-1234567890',
        'address': '123 Farm Road, India',
        'social_links': {'facebook': '', 'twitter': '', 'instagram': ''},
    }
    email_settings = {
        'order_confirmation': 'Thank you for your order!',
        'status_update': 'Your order status has changed.',
        'welcome': 'Welcome to SmartFarming!',
    }
    payment_settings = {
        'gateway': 'Stripe',
        'currency': 'INR',
        'tax': '18%',
        'shipping_rates': 'Standard',
    }
    notification_settings = {
        'email_notifications': True,
        'sms_notifications': False,
        'low_stock_alerts': True,
        'new_order_alerts': True,
        'new_user_alerts': True,
    }
    context = {
        'site_settings': site_settings,
        'email_settings': email_settings,
        'payment_settings': payment_settings,
        'notification_settings': notification_settings,
    }
    return render(request, 'settings/settings.html', context)
