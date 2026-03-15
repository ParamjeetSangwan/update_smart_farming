# reports/views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from orders.models import Order
from django.db.models import Sum, Count
from django.utils import timezone
import datetime

@staff_member_required
def sales_report_view(request):
    today = timezone.now().date()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    orders_qs = Order.objects.all()
    if start_date:
        orders_qs = orders_qs.filter(created_at__date__gte=start_date)
    if end_date:
        orders_qs = orders_qs.filter(created_at__date__lte=end_date)

    total_sales = orders_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0
    sales_by_product = []  # Placeholder, requires product linkage
    sales_by_category = [] # Placeholder, requires category linkage
    revenue_trends = []    # Placeholder for chart data

    context = {
        'orders': orders_qs.order_by('-created_at'),
        'total_sales': total_sales,
        'sales_by_product': sales_by_product,
        'sales_by_category': sales_by_category,
        'revenue_trends': revenue_trends,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/sales_report.html', context)

from users.models import UserProfile
from django.contrib.auth.models import User
from django.db.models import Count, Sum

@staff_member_required
def user_report_view(request):
    users_qs = User.objects.all()
    user_growth = users_qs.extra({'month': "strftime('%%Y-%%m', date_joined)"}).values('month').annotate(count=Count('id')).order_by('month')
    user_activity = users_qs.annotate(order_count=Count('orders')).order_by('-order_count')[:10]
    user_retention = []  # Placeholder for retention calculation
    top_customers = users_qs.annotate(total_spent=Sum('orders__total_price')).order_by('-total_spent')[:10]

    context = {
        'user_growth': user_growth,
        'user_activity': user_activity,
        'user_retention': user_retention,
        'top_customers': top_customers,
    }
    return render(request, 'reports/user_report.html', context)

from marketplace.models import Tool, Pesticide

@staff_member_required
def inventory_report_view(request):
    tools_qs = Tool.objects.all()
    pesticides_qs = Pesticide.objects.all()
    # Placeholder: If stock field exists, filter low/out-of-stock
    low_stock_tools = []
    out_of_stock_tools = []
    low_stock_pesticides = []
    out_of_stock_pesticides = []

    context = {
        'tools': tools_qs,
        'pesticides': pesticides_qs,
        'low_stock_tools': low_stock_tools,
        'out_of_stock_tools': out_of_stock_tools,
        'low_stock_pesticides': low_stock_pesticides,
        'out_of_stock_pesticides': out_of_stock_pesticides,
    }
    return render(request, 'reports/inventory_report.html', context)
