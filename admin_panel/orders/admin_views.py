# orders/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from orders.models import Order
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum

@staff_member_required
def order_list_view(request):
    search = request.GET.get('search', '')
    filter_status = request.GET.get('status', '')
    filter_date = request.GET.get('date', '')
    filter_amount_min = request.GET.get('amount_min', '')
    filter_amount_max = request.GET.get('amount_max', '')

    orders_qs = Order.objects.all()
    if search:
        orders_qs = orders_qs.filter(Q(id__icontains=search) | Q(user__username__icontains=search))
    if filter_status:
        orders_qs = orders_qs.filter(status__icontains=filter_status)
    if filter_date:
        orders_qs = orders_qs.filter(created_at__date=filter_date)
    if filter_amount_min:
        orders_qs = orders_qs.filter(total_price__gte=float(filter_amount_min))
    if filter_amount_max:
        orders_qs = orders_qs.filter(total_price__lte=float(filter_amount_max))

    paginator = Paginator(orders_qs.order_by('-created_at'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics
    total_orders_today = orders_qs.filter(created_at__date=timezone.now().date()).count()
    total_orders_week = orders_qs.filter(created_at__date__gte=timezone.now().date()-timezone.timedelta(days=7)).count()
    total_orders_month = orders_qs.filter(created_at__date__gte=timezone.now().date()-timezone.timedelta(days=30)).count()
    revenue_today = orders_qs.filter(created_at__date=timezone.now().date()).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_week = orders_qs.filter(created_at__date__gte=timezone.now().date()-timezone.timedelta(days=7)).aggregate(Sum('total_price'))['total_price__sum'] or 0
    revenue_month = orders_qs.filter(created_at__date__gte=timezone.now().date()-timezone.timedelta(days=30)).aggregate(Sum('total_price'))['total_price__sum'] or 0
    orders_by_status = orders_qs.values('status').annotate(count=Count('id')).order_by('-count')

    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_amount_min': filter_amount_min,
        'filter_amount_max': filter_amount_max,
        'total_orders_today': total_orders_today,
        'total_orders_week': total_orders_week,
        'total_orders_month': total_orders_month,
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,
        'orders_by_status': orders_by_status,
    }
    return render(request, 'orders/order_list.html', context)

@staff_member_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/order_detail.html', {'order': order})

from django import forms
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'total_price']

@staff_member_required
def order_edit_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    form = OrderForm(request.POST or None, instance=order)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin_order_list')
    return render(request, 'orders/order_edit.html', {'form': form, 'order': order})

@staff_member_required
def order_delete_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        return redirect('admin_order_list')
    return render(request, 'orders/order_delete.html', {'order': order})
