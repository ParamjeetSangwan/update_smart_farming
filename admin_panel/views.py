# admin_panel/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import json

from marketplace.models import Tool, Pesticide
from orders.models import Order, OrderItem
from crops.models import Crop
from ai_recommendations.models import AIQueryHistory
from users.models import UserProfile, Notification, Announcement, AdminTwoFactor


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            messages.error(request, 'Access denied. Admin only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ══════════════════════════════════════════
# 1. DASHBOARD
# ══════════════════════════════════════════
@admin_required
def dashboard_view(request):
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = User.objects.count()
    total_tools = Tool.objects.count()
    total_pesticides = Pesticide.objects.count()
    total_products = total_tools + total_pesticides
    total_crops = Crop.objects.count()
    total_ai_queries = AIQueryHistory.objects.count()
    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_this_week = Order.objects.filter(created_at__gte=week_ago).count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    new_users_month = User.objects.filter(date_joined__gte=month_ago).count()
    user_growth = round((new_users_month / max(total_users - new_users_month, 1)) * 100, 1)

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_ai_queries = AIQueryHistory.objects.select_related('user').order_by('-timestamp')[:5]

    revenue_by_day = (
        Order.objects.filter(created_at__gte=month_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day').annotate(total=Sum('total_price')).order_by('day')
    )
    revenue_labels, revenue_values = [], []
    for i in range(30):
        day = (now - timedelta(days=29 - i)).date()
        revenue_labels.append(day.strftime('%b %d'))
        found = next((r['total'] for r in revenue_by_day if r['day'] == day), 0)
        revenue_values.append(float(found or 0))

    tools_by_cat = list(Tool.objects.values('category').annotate(count=Count('id')))
    cat_labels = [t['category'] for t in tools_by_cat] + ['Pesticides']
    cat_values = [t['count'] for t in tools_by_cat] + [total_pesticides]

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_tools': total_tools,
        'total_pesticides': total_pesticides,
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_this_week': orders_this_week,
        'total_revenue': total_revenue,
        'total_crops': total_crops,
        'total_ai_queries': total_ai_queries,
        'user_growth': user_growth,
        'new_users_month': new_users_month,
        'recent_orders': recent_orders,
        'recent_users': recent_users,
        'recent_ai_queries': recent_ai_queries,
        'revenue_chart_data': json.dumps({'labels': revenue_labels, 'values': revenue_values}),
        'category_chart_data': json.dumps({'labels': cat_labels, 'values': cat_values}),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ══════════════════════════════════════════
# 2. RECENT ACTIVITY
# ══════════════════════════════════════════
@admin_required
def admin_activity_view(request):
    activities = []
    for order in Order.objects.select_related('user').order_by('-created_at')[:20]:
        activities.append({
            'type': 'order', 'icon': 'shopping-bag',
            'text': f'<strong>{order.user.username}</strong> placed an order worth ₹{order.total_price}',
            'time': order.created_at, 'link': f'/myadmin/orders/{order.id}/',
        })
    for user in User.objects.order_by('-date_joined')[:20]:
        activities.append({
            'type': 'user', 'icon': 'user-plus',
            'text': f'<strong>{user.username}</strong> joined SmartFarm',
            'time': user.date_joined, 'link': f'/myadmin/users/{user.id}/',
        })
    for query in AIQueryHistory.objects.select_related('user').order_by('-timestamp')[:20]:
        activities.append({
            'type': 'product', 'icon': 'robot',
            'text': f'<strong>{query.user.username}</strong> asked AI: "{query.prompt[:60]}..."',
            'time': query.timestamp, 'link': None,
        })
    activities.sort(key=lambda x: x['time'], reverse=True)
    activities = activities[:50]
    return render(request, 'admin_panel/activity.html', {
        'activities': activities, 'total_activities': len(activities),
    })


# ══════════════════════════════════════════
# 3. USER MANAGEMENT
# ══════════════════════════════════════════
@admin_required
def admin_users_view(request):
    users = User.objects.annotate(order_count=Count('orders')).order_by('-date_joined')
    search = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    elif status == 'staff':
        users = users.filter(is_staff=True)
    elif status == 'blocked':
        users = users.filter(profile__is_blocked=True)
    context = {
        'users': users, 'search': search, 'status': status,
        'total': users.count(),
        'active_count': User.objects.filter(is_active=True).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'blocked_count': UserProfile.objects.filter(is_blocked=True).count(),
    }
    return render(request, 'admin_panel/users.html', context)


@admin_required
def admin_user_detail_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(user=user_obj).order_by('-created_at')
    ai_queries = AIQueryHistory.objects.filter(user=user_obj).order_by('-timestamp')[:10]
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    two_factor = AdminTwoFactor.objects.filter(user=user_obj).first()
    context = {
        'user_obj': user_obj, 'orders': orders,
        'ai_queries': ai_queries, 'total_spent': total_spent,
        'order_count': orders.count(),
        'two_factor': two_factor,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def admin_user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate yourself!")
        return redirect('admin_users')
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    messages.success(request, f"User {user_obj.username} {'activated' if user_obj.is_active else 'deactivated'}.")
    return redirect('admin_users')


@admin_required
def admin_user_delete(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot delete yourself!")
        return redirect('admin_users')
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"User '{username}' deleted.")
    return redirect('admin_users')


@admin_required
def admin_user_make_staff(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_staff = not user_obj.is_staff
    user_obj.save()
    messages.success(request, f"{user_obj.username} is now {'admin' if user_obj.is_staff else 'regular user'}.")
    return redirect('admin_users')


# ── FEATURE: Block / Unban User ──
@admin_required
def admin_user_block(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot block yourself!")
        return redirect('admin_users')
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Violated terms of service')
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
        profile.is_blocked = True
        profile.blocked_reason = reason
        profile.save()
        # Also deactivate
        user_obj.is_active = False
        user_obj.save()
        # Notify user
        Notification.objects.create(
            user=user_obj,
            title='Account Blocked',
            message=f'Your account has been blocked. Reason: {reason}',
            notification_type='alert'
        )
        messages.success(request, f"User '{user_obj.username}' has been blocked.")
    return redirect('admin_users')


@admin_required
def admin_user_unblock(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
        profile.is_blocked = False
        profile.blocked_reason = None
        profile.save()
        user_obj.is_active = True
        user_obj.save()
        Notification.objects.create(
            user=user_obj,
            title='Account Unblocked',
            message='Your account has been unblocked. Welcome back!',
            notification_type='info'
        )
        messages.success(request, f"User '{user_obj.username}' has been unblocked.")
    return redirect('admin_users')


# ── FEATURE: Toggle 2FA for admin user ──
@admin_required
def admin_user_toggle_2fa(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    two_factor, _ = AdminTwoFactor.objects.get_or_create(user=user_obj)
    two_factor.is_enabled = not two_factor.is_enabled
    two_factor.save()
    status = "enabled" if two_factor.is_enabled else "disabled"
    messages.success(request, f"2FA {status} for {user_obj.username}.")
    return redirect('admin_user_detail', user_id=user_id)


# ══════════════════════════════════════════
# 4. PRODUCT MANAGEMENT
# ══════════════════════════════════════════
@admin_required
def admin_products_view(request):
    tools = Tool.objects.all()
    pesticides = Pesticide.objects.all()
    search = request.GET.get('q', '')
    product_type = request.GET.get('type', '')
    if search:
        tools = tools.filter(Q(name__icontains=search) | Q(description__icontains=search))
        pesticides = pesticides.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if product_type == 'tools':
        pesticides = Pesticide.objects.none()
    elif product_type == 'pesticides':
        tools = Tool.objects.none()
    context = {
        'tools': tools, 'pesticides': pesticides,
        'search': search, 'product_type': product_type,
        'total_tools': Tool.objects.count(),
        'total_pesticides': Pesticide.objects.count(),
        'categories': Tool.objects.values_list('category', flat=True).distinct(),
    }
    return render(request, 'admin_panel/products.html', context)


@admin_required
def admin_product_add_view(request):
    if request.method == 'POST':
        product_type = request.POST.get('product_type')
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        if product_type == 'tool':
            Tool.objects.create(name=name, description=description, price=price,
                                category=request.POST.get('category', 'General'), image=image)
            messages.success(request, f"Tool '{name}' added!")
        elif product_type == 'pesticide':
            Pesticide.objects.create(name=name, description=description, price=price, image=image)
            messages.success(request, f"Pesticide '{name}' added!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_add.html')


@admin_required
def admin_tool_edit_view(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        tool.name = request.POST.get('name')
        tool.description = request.POST.get('description')
        tool.price = request.POST.get('price')
        tool.category = request.POST.get('category', 'General')
        if request.FILES.get('image'):
            tool.image = request.FILES.get('image')
        tool.save()
        messages.success(request, f"Tool '{tool.name}' updated!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_edit.html', {'product': tool, 'product_type': 'tool'})


@admin_required
def admin_pesticide_edit_view(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    if request.method == 'POST':
        pesticide.name = request.POST.get('name')
        pesticide.description = request.POST.get('description')
        pesticide.price = request.POST.get('price')
        if request.FILES.get('image'):
            pesticide.image = request.FILES.get('image')
        pesticide.save()
        messages.success(request, f"Pesticide '{pesticide.name}' updated!")
        return redirect('admin_products')
    return render(request, 'admin_panel/product_edit.html', {'product': pesticide, 'product_type': 'pesticide'})


@admin_required
def admin_tool_delete_view(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        name = tool.name
        tool.delete()
        messages.success(request, f"Tool '{name}' deleted!")
    return redirect('admin_products')


@admin_required
def admin_pesticide_delete_view(request, pesticide_id):
    pesticide = get_object_or_404(Pesticide, id=pesticide_id)
    if request.method == 'POST':
        name = pesticide.name
        pesticide.delete()
        messages.success(request, f"Pesticide '{name}' deleted!")
    return redirect('admin_products')


# ══════════════════════════════════════════
# 5. ORDER MANAGEMENT
# ══════════════════════════════════════════
@admin_required
def admin_orders_view(request):
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    search = request.GET.get('q', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if search:
        orders = orders.filter(Q(user__username__icontains=search) | Q(id__icontains=search))
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    context = {
        'orders': orders, 'search': search,
        'date_from': date_from, 'date_to': date_to,
        'total_orders': orders.count(),
        'total_revenue': orders.aggregate(total=Sum('total_price'))['total'] or 0,
    }
    return render(request, 'admin_panel/orders.html', context)


@admin_required
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()
    for item in items:
        if item.item_type == 'tool':
            item.product = Tool.objects.filter(id=item.item_id).first()
        elif item.item_type == 'pesticide':
            item.product = Pesticide.objects.filter(id=item.item_id).first()
    return render(request, 'admin_panel/order_detail.html', {'order': order, 'items': items})


@admin_required
def admin_order_delete_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, f"Order #{order_id} deleted!")
    return redirect('admin_orders')


# ══════════════════════════════════════════
# 6. CROP MANAGEMENT
# ══════════════════════════════════════════
@admin_required
def admin_crops_view(request):
    crops = Crop.objects.all().order_by('country', 'crop')
    search = request.GET.get('q', '')
    country_filter = request.GET.get('country', '')
    season_filter = request.GET.get('season', '')
    if search:
        crops = crops.filter(Q(crop__icontains=search) | Q(country__icontains=search))
    if country_filter:
        crops = crops.filter(country=country_filter)
    if season_filter:
        crops = crops.filter(season__icontains=season_filter)
    paginator = Paginator(crops, 50)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    context = {
        'crops': crops, 'page_obj': page_obj,
        'search': search, 'country_filter': country_filter, 'season_filter': season_filter,
        'countries': Crop.objects.values_list('country', flat=True).distinct().order_by('country'),
        'seasons': Crop.objects.values_list('season', flat=True).distinct(),
        'total': Crop.objects.count(),
    }
    return render(request, 'admin_panel/crops.html', context)


@admin_required
def admin_crop_add_view(request):
    if request.method == 'POST':
        Crop.objects.create(
            country=request.POST.get('country'), crop=request.POST.get('crop'),
            soil_type=request.POST.get('soil_type'), temperature=request.POST.get('temperature'),
            season=request.POST.get('season'), category=request.POST.get('category'),
        )
        messages.success(request, "Crop added!")
        return redirect('admin_crops')
    return render(request, 'admin_panel/crop_add.html')


@admin_required
def admin_crop_edit_view(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    if request.method == 'POST':
        crop.country = request.POST.get('country')
        crop.crop = request.POST.get('crop')
        crop.soil_type = request.POST.get('soil_type')
        crop.temperature = request.POST.get('temperature')
        crop.season = request.POST.get('season')
        crop.category = request.POST.get('category')
        crop.save()
        messages.success(request, f"Crop '{crop.crop}' updated!")
        return redirect('admin_crops')
    return render(request, 'admin_panel/crop_edit.html', {'crop': crop})


@admin_required
def admin_crop_delete_view(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    if request.method == 'POST':
        name = crop.crop
        crop.delete()
        messages.success(request, f"Crop '{name}' deleted!")
    return redirect('admin_crops')


# ══════════════════════════════════════════
# 7. AI HISTORY
# ══════════════════════════════════════════
@admin_required
def admin_ai_history_view(request):
    queries = AIQueryHistory.objects.select_related('user').order_by('-timestamp')
    search = request.GET.get('q', '')
    user_filter = request.GET.get('user', '')
    if search:
        queries = queries.filter(Q(prompt__icontains=search) | Q(response__icontains=search))
    if user_filter:
        queries = queries.filter(user__username__icontains=user_filter)
    context = {
        'queries': queries, 'search': search, 'user_filter': user_filter,
        'total': AIQueryHistory.objects.count(),
        'total_users_queried': AIQueryHistory.objects.values('user').distinct().count(),
    }
    return render(request, 'admin_panel/ai_history.html', context)


@admin_required
def admin_ai_delete_view(request, query_id):
    query = get_object_or_404(AIQueryHistory, id=query_id)
    if request.method == 'POST':
        query.delete()
        messages.success(request, "AI query deleted.")
    return redirect('admin_ai_history')


# ══════════════════════════════════════════
# 8. ANNOUNCEMENTS
# ══════════════════════════════════════════
@admin_required
def admin_announcements_view(request):
    announcements = Announcement.objects.all()
    return render(request, 'admin_panel/announcements.html', {'announcements': announcements})


@admin_required
def admin_announcement_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        send_email = request.POST.get('send_email') == 'on'

        # Create announcement
        announcement = Announcement.objects.create(
            title=title,
            message=message,
            created_by=request.user,
            send_email=send_email
        )

        # Create notification for ALL users
        users = User.objects.filter(is_active=True)
        notifications = [
            Notification(
                user=user,
                title=f'📢 {title}',
                message=message,
                notification_type='announcement'
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)

        # Send email to all users if selected
        if send_email:
            user_emails = list(users.exclude(email='').values_list('email', flat=True))
            if user_emails:
                try:
                    send_mail(
                        f'📢 SmartFarming: {title}',
                        f'{message}\n\n— SmartFarming Admin Team 🌾',
                        settings.DEFAULT_FROM_EMAIL,
                        user_emails,
                        fail_silently=True,
                    )
                except Exception:
                    pass

        messages.success(request, f'✅ Announcement sent to {users.count()} users!')
        return redirect('admin_announcements')

    return render(request, 'admin_panel/announcement_create.html')


@admin_required
def admin_announcement_delete(request, ann_id):
    announcement = get_object_or_404(Announcement, id=ann_id)
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "Announcement deleted.")
    return redirect('admin_announcements')


# ══════════════════════════════════════════
# 9. REPORTS
# ══════════════════════════════════════════
@admin_required
def admin_reports_view(request):
    top_products = (
        OrderItem.objects.values('name')
        .annotate(total_sold=Sum('quantity'), revenue=Sum('price'))
        .order_by('-total_sold')[:10]
    )
    top_customers = (
        Order.objects.values('user__username')
        .annotate(order_count=Count('id'), total_spent=Sum('total_price'))
        .order_by('-total_spent')[:10]
    )
    context = {
        'top_products': top_products, 'top_customers': top_customers,
        'total_revenue': Order.objects.aggregate(t=Sum('total_price'))['t'] or 0,
        'total_orders': Order.objects.count(),
        'total_users': User.objects.count(),
        'total_crops': Crop.objects.count(),
    }
    return render(request, 'admin_panel/reports.html', context)


# ══════════════════════════════════════════
# 10. SETTINGS
# ══════════════════════════════════════════
@admin_required
def admin_settings_view(request):
    return render(request, 'admin_panel/settings.html')