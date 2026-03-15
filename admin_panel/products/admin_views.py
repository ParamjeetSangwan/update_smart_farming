# products/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from marketplace.models import Tool, Pesticide
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ToolForm, PesticideForm
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def product_list_view(request):
    search = request.GET.get('search', '')
    filter_category = request.GET.get('category', '')
    filter_stock = request.GET.get('stock', '')

    tools_qs = Tool.objects.all()
    pesticides_qs = Pesticide.objects.all()
    if search:
        tools_qs = tools_qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        pesticides_qs = pesticides_qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if filter_category:
        tools_qs = tools_qs.filter(category__icontains=filter_category)
    # Stock filter placeholder (if stock field exists)

    products = list(tools_qs) + list(pesticides_qs)
    paginator = Paginator(products, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics
    top_selling_products = []  # Placeholder, requires sales/order data
    low_stock_products = []    # Placeholder, requires stock field
    revenue_by_product = []    # Placeholder, requires sales/order data
    products_by_category = tools_qs.values('category').annotate(count=Count('id')).order_by('-count')

    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_category': filter_category,
        'filter_stock': filter_stock,
        'top_selling_products': top_selling_products,
        'low_stock_products': low_stock_products,
        'revenue_by_product': revenue_by_product,
        'products_by_category': products_by_category,
    }
    return render(request, 'products/product_list.html', context)

@staff_member_required
def product_add_view(request):
    tool_form = ToolForm(request.POST or None, request.FILES or None)
    pesticide_form = PesticideForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if 'add_tool' in request.POST and tool_form.is_valid():
            tool_form.save()
            return redirect('admin_product_list')
        elif 'add_pesticide' in request.POST and pesticide_form.is_valid():
            pesticide_form.save()
            return redirect('admin_product_list')
    return render(request, 'products/product_add.html', {'tool_form': tool_form, 'pesticide_form': pesticide_form})

@staff_member_required
def product_edit_view(request, product_id, product_type):
    if product_type == 'tool':
        product = get_object_or_404(Tool, id=product_id)
        form = ToolForm(request.POST or None, request.FILES or None, instance=product)
    else:
        product = get_object_or_404(Pesticide, id=product_id)
        form = PesticideForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('admin_product_list')
    return render(request, 'products/product_edit.html', {'form': form, 'product': product, 'product_type': product_type})

@staff_member_required
def product_delete_view(request, product_id, product_type):
    if product_type == 'tool':
        product = get_object_or_404(Tool, id=product_id)
    else:
        product = get_object_or_404(Pesticide, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_product_list')
    return render(request, 'products/product_delete.html', {'product': product, 'product_type': product_type})

@staff_member_required
def product_detail_view(request, product_id):
    # Placeholder for product detail
    context = {}
    return render(request, 'products/product_detail.html', context)
