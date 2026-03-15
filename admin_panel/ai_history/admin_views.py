# ai_history/admin_views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from ai_recommendations.models import AIQueryHistory
from django.core.paginator import Paginator
from django.db.models import Q, Count

@staff_member_required
def ai_history_view(request):
    search = request.GET.get('search', '')
    filter_user = request.GET.get('user', '')
    filter_date = request.GET.get('date', '')

    queries_qs = AIQueryHistory.objects.all()
    if search:
        queries_qs = queries_qs.filter(Q(prompt__icontains=search) | Q(response__icontains=search))
    if filter_user:
        queries_qs = queries_qs.filter(user__username__icontains=filter_user)
    if filter_date:
        queries_qs = queries_qs.filter(timestamp__date=filter_date)

    paginator = Paginator(queries_qs.order_by('-timestamp'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics
    total_queries = queries_qs.count()
    queries_by_user = queries_qs.values('user__username').annotate(count=Count('id')).order_by('-count')
    popular_topics = []  # Placeholder for topic analysis

    context = {
        'page_obj': page_obj,
        'search': search,
        'filter_user': filter_user,
        'filter_date': filter_date,
        'total_queries': total_queries,
        'queries_by_user': queries_by_user,
        'popular_topics': popular_topics,
    }
    return render(request, 'ai_history/ai_history.html', context)
