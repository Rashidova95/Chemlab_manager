from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.samples.models import Sample
from apps.experiments.models import Experiment
from apps.inventory.models import Chemical
from apps.users.models import CustomUser


@extend_schema(tags=['Dashboard'])
class DashboardStatsView(APIView):
    """
    FR-11: Dashboard statistikasi.
    GET /api/v1/dashboard/stats/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_ago  = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # --- Namunalar statistikasi ---
        samples_total   = Sample.objects.count()
        samples_today   = Sample.objects.filter(received_at__date=today).count()
        samples_week    = Sample.objects.filter(received_at__date__gte=week_ago).count()
        samples_month   = Sample.objects.filter(received_at__date__gte=month_ago).count()

        # --- Holat bo'yicha taqsimot (pie chart uchun) ---
        status_counts = Sample.objects.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in status_counts}

        # --- Tajribalar statistikasi ---
        experiments_total    = Experiment.objects.count()
        experiments_approved = Experiment.objects.filter(status='approved').count()
        experiments_pending  = Experiment.objects.filter(status='review').count()

        # --- Laborant faolligi reytingi ---
        laborant_activity = (
            Sample.objects
            .filter(received_at__date__gte=month_ago)
            .values('received_by__email', 'received_by__first_name', 'received_by__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        laborant_rating = [
            {
                'email': item['received_by__email'],
                'name':  f"{item['received_by__first_name']} {item['received_by__last_name']}".strip(),
                'count': item['count'],
            }
            for item in laborant_activity
        ]

        # --- Inventar holati xulosa ---
        chemicals_total    = Chemical.objects.filter(is_active=True).count()
        chemicals_low      = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_low_stock)
        chemicals_expiring = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_expiring_soon)
        chemicals_expired  = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_expired)

        return Response({
            'samples': {
                'total':   samples_total,
                'today':   samples_today,
                'week':    samples_week,
                'month':   samples_month,
                'by_status': status_data,
            },
            'experiments': {
                'total':    experiments_total,
                'approved': experiments_approved,
                'pending':  experiments_pending,
            },
            'laborant_rating': laborant_rating,
            'inventory': {
                'total':    chemicals_total,
                'low':      chemicals_low,
                'expiring': chemicals_expiring,
                'expired':  chemicals_expired,
            },
        })