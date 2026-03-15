# dashboard/views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from users.models import UserProfile
from django.contrib.auth.models import User
from marketplace.models import Tool, Pesticide
from orders.models import Order
from crops.models import Crop
from ai_recommendations.models import AIQueryHistory
from django.db.models import Sum, Count

@staff_member_required
def dashboard_view(request):
    total_users = User.objects.count()
    total_tools = Tool.objects.count()
    total_pesticides = Pesticide.objects.count()
    total_products = total_tools + total_pesticides
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_crops = Crop.objects.count()
    total_ai_queries = AIQueryHistory.objects.count()

    # Example: Average order value
    avg_order_value = total_revenue / total_orders if total_orders else 0

    # Example: Conversion rate (users who placed orders / total users)
    users_with_orders = Order.objects.values('user').distinct().count()
    conversion_rate = (users_with_orders / total_users) * 100 if total_users else 0

    # Revenue over last 30 days
    from django.utils import timezone
    import datetime
    today = timezone.now().date()
    last_30_days = [today - datetime.timedelta(days=i) for i in range(29, -1, -1)]
    revenue_by_day = []
    for day in last_30_days:
        day_orders = Order.objects.filter(created_at__date=day)
        day_revenue = day_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        revenue_by_day.append(day_revenue)

    # Orders per week (last 8 weeks)
    orders_by_week = []
    week_labels = []
    for i in range(7, -1, -1):
        week_start = today - datetime.timedelta(days=i*7)
        week_end = week_start + datetime.timedelta(days=6)
        week_orders = Order.objects.filter(created_at__date__gte=week_start, created_at__date__lte=week_end)
        orders_by_week.append(week_orders.count())
        week_labels.append(f"Week {week_start.strftime('%W')}")

    # Recent activity feeds
    latest_orders = Order.objects.order_by('-created_at')[:10]
    latest_users = User.objects.order_by('-date_joined')[:5]
    recent_ai_queries = AIQueryHistory.objects.order_by('-timestamp')[:10]

    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_tools': total_tools,
        'total_pesticides': total_pesticides,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_crops': total_crops,
        'total_ai_queries': total_ai_queries,
        'avg_order_value': avg_order_value,
        'conversion_rate': conversion_rate,
        'revenue_by_day': revenue_by_day,
        'last_30_days': [d.strftime('%Y-%m-%d') for d in last_30_days],
        'orders_by_week': orders_by_week,
        'week_labels': week_labels,
        'latest_orders': latest_orders,
        'latest_users': latest_users,
        'recent_ai_queries': recent_ai_queries,
    }
    return render(request, 'dashboard/dashboard.html', context)
