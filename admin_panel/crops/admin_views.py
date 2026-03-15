# crops/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from crops.models import Crop
from django.core.paginator import Paginator
from django.db.models import Q, Count

@staff_member_required
def crop_list_view(request):
    search = request.GET.get('search', '')
    filter_country = request.GET.get('country', '')
    filter_soil = request.GET.get('soil', '')
    filter_season = request.GET.get('season', '')
    filter_category = request.GET.get('category', '')

    crops_qs = Crop.objects.all()
    if search:
        crops_qs = crops_qs.filter(Q(crop__icontains=search) | Q(country__icontains=search))
    if filter_country:
        crops_qs = crops_qs.filter(country__icontains=filter_country)
    if filter_soil:
        crops_qs = crops_qs.filter(soil_type__icontains=filter_soil)
    if filter_season:
        crops_qs = crops_qs.filter(season__icontains=filter_season)
    if filter_category:
        crops_qs = crops_qs.filter(category__icontains=filter_category)

    paginator = Paginator(crops_qs.order_by('crop'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics
    crops_by_country = crops_qs.values('country').annotate(count=Count('id')).order_by('-count')
    crops_by_season = crops_qs.values('season').annotate(count=Count('id')).order_by('-count')
    total_crops = crops_qs.count()

    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_country': filter_country,
        'filter_soil': filter_soil,
        'filter_season': filter_season,
        'filter_category': filter_category,
        'crops_by_country': crops_by_country,
        'crops_by_season': crops_by_season,
        'total_crops': total_crops,
    }
    return render(request, 'crops/crop_list.html', context)

    # Crop CRUD forms
    from django import forms
    class CropForm(forms.ModelForm):
        class Meta:
            model = Crop
            fields = ['country', 'crop', 'soil_type', 'temperature', 'season', 'category']

    @staff_member_required
    def crop_add_view(request):
        form = CropForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('admin_crop_list')
        return render(request, 'crops/crop_edit.html', {'form': form, 'is_add': True})

    @staff_member_required
    def crop_edit_view(request, crop_id):
        crop = get_object_or_404(Crop, id=crop_id)
        form = CropForm(request.POST or None, instance=crop)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('admin_crop_list')
        return render(request, 'crops/crop_edit.html', {'form': form, 'is_add': False, 'crop': crop})

    @staff_member_required
    def crop_delete_view(request, crop_id):
        crop = get_object_or_404(Crop, id=crop_id)
        if request.method == 'POST':
            crop.delete()
            return redirect('admin_crop_list')
        return render(request, 'crops/crop_delete.html', {'crop': crop})
