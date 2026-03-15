# users/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from orders.models import Order
from users.models import UserProfile
from django.contrib.auth.models import User

@staff_member_required
def user_list_view(request):
    search = request.GET.get('search', '')
    filter_location = request.GET.get('location', '')
    filter_active = request.GET.get('active', '')
    filter_has_orders = request.GET.get('has_orders', '')

    users_qs = User.objects.all()
    if search:
        users_qs = users_qs.filter(Q(username__icontains=search) | Q(email__icontains=search) | Q(profile__name__icontains=search))
    if filter_location:
        users_qs = users_qs.filter(profile__location__icontains=filter_location)
    if filter_active:
        users_qs = users_qs.filter(is_active=(filter_active == 'true'))
    if filter_has_orders:
        if filter_has_orders == 'true':
            users_qs = users_qs.annotate(order_count=Count('orders')).filter(order_count__gt=0)
        else:
            users_qs = users_qs.annotate(order_count=Count('orders')).filter(order_count=0)

    paginator = Paginator(users_qs.order_by('-date_joined'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics
    most_active_users = users_qs.annotate(order_count=Count('orders')).order_by('-order_count')[:5]
    highest_spending_users = users_qs.annotate(total_spent=Sum('orders__total_price')).order_by('-total_spent')[:5]
    users_by_location = users_qs.values('profile__location').annotate(count=Count('id')).order_by('-count')
    new_users_trend = users_qs.extra({'month': "strftime('%%Y-%%m', date_joined)"}).values('month').annotate(count=Count('id')).order_by('month')

    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_location': filter_location,
        'filter_active': filter_active,
        'filter_has_orders': filter_has_orders,
        'most_active_users': most_active_users,
        'highest_spending_users': highest_spending_users,
        'users_by_location': users_by_location,
        'new_users_trend': new_users_trend,
    }
    return render(request, 'users/user_list.html', context)

@staff_member_required
def user_detail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)
    return render(request, 'users/user_detail.html', {'user': user, 'profile': profile})

# User CRUD forms
from django import forms
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_active']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['name', 'location']

@staff_member_required
def user_add_view(request):
    user_form = UserForm(request.POST or None)
    profile_form = UserProfileForm(request.POST or None)
    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            return redirect('admin_user_list')
    return render(request, 'users/user_edit.html', {'user_form': user_form, 'profile_form': profile_form, 'is_add': True})

@staff_member_required
def user_edit_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, 'profile', None)
    user_form = UserForm(request.POST or None, instance=user)
    profile_form = UserProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('admin_user_list')
    return render(request, 'users/user_edit.html', {'user_form': user_form, 'profile_form': profile_form, 'is_add': False})

@staff_member_required
def user_delete_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('admin_user_list')
    return render(request, 'users/user_delete.html', {'user': user})
