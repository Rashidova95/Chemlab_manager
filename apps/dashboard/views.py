from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.experiments.models import Experiment
from apps.inventory.models import Chemical
from apps.samples.models import Sample
from apps.users.permissions import IsChemist


@extend_schema(tags=['Dashboard'], responses={200: dict})
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # --- Namunalar statistikasi ---
        samples_total = Sample.objects.count()
        samples_today = Sample.objects.filter(received_at__date=today).count()
        samples_week = Sample.objects.filter(received_at__date__gte=week_ago).count()
        samples_month = Sample.objects.filter(received_at__date__gte=month_ago).count()

        # --- Holat bo'yicha taqsimot (pie chart uchun) ---
        status_counts = Sample.objects.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in status_counts}

        # --- Tajribalar statistikasi ---
        experiments_total = Experiment.objects.count()
        experiments_approved = Experiment.objects.filter(status='approved').count()
        experiments_pending = Experiment.objects.filter(status='review').count()

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
                'name': f"{item['received_by__first_name']} {item['received_by__last_name']}".strip(),
                'count': item['count'],
            }
            for item in laborant_activity
        ]

        # --- Inventar holati xulosa ---
        chemicals_total = Chemical.objects.filter(is_active=True).count()
        chemicals_low = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_low_stock)
        chemicals_expiring = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_expiring_soon)
        chemicals_expired = sum(1 for c in Chemical.objects.filter(is_active=True) if c.is_expired)

        return Response({
            'samples': {
                'total': samples_total,
                'today': samples_today,
                'week': samples_week,
                'month': samples_month,
                'by_status': status_data,
            },
            'experiments': {
                'total': experiments_total,
                'approved': experiments_approved,
                'pending': experiments_pending,
            },
            'laborant_rating': laborant_rating,
            'inventory': {
                'total': chemicals_total,
                'low': chemicals_low,
                'expiring': chemicals_expiring,
                'expired': chemicals_expired,
            },
        })


@extend_schema(tags=['Dashboard'], responses={200: dict})
class ExposureLedgerView(APIView):
    """
    Xodimning kimyoviy xavf ta'siri hisoboti — mavjud ma'lumotlar (kim,
    qaysi tajribada, qanday xavf darajasidagi reaktivlar bilan ishlagani)
    asosida, yangi ma'lumot kiritmasdan hisoblanadi.

    GET /api/v1/dashboard/exposure/?days=90
    Faqat admin/chemist ko'radi — bu xodimlar sog'ligini nazorat qilish
    uchun boshqaruv ma'lumoti.
    """
    permission_classes = [IsAuthenticated, IsChemist]

    # Qancha kundan buyon hisoblansin (standart — 90 kun)
    DEFAULT_DAYS = 90
    # Shu darajadan boshlab "yuqori xavf" deb hisoblanadi (Chemical.HAZARD_CHOICES: 3=Yuqori, 4=Juda yuqori)
    HIGH_HAZARD_THRESHOLD = 3
    # Shu oy ichida nechta yuqori xavfli ishdan keyin ogohlantirish chiqsin
    ALERT_THRESHOLD = 20

    def get(self, request):
        days = int(request.query_params.get('days', self.DEFAULT_DAYS))
        since = timezone.now() - timedelta(days=days)

        experiments = (
            Experiment.objects
            .filter(created_at__gte=since, performed_by__isnull=False)
            .select_related('performed_by')
            .prefetch_related('chemicals_used')
        )

        # { user_id: {"name": ..., "total_exposures": 0, "high_hazard_exposures": 0} }
        ledger = {}

        for exp in experiments:
            user = exp.performed_by
            entry = ledger.setdefault(user.id, {
                'user_id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'email': user.email,
                'total_exposures': 0,
                'high_hazard_exposures': 0,
            })
            for chem in exp.chemicals_used.all():
                entry['total_exposures'] += 1
                if chem.hazard_level >= self.HIGH_HAZARD_THRESHOLD:
                    entry['high_hazard_exposures'] += 1

        results = sorted(ledger.values(), key=lambda x: -x['high_hazard_exposures'])
        for r in results:
            r['over_threshold'] = r['high_hazard_exposures'] >= self.ALERT_THRESHOLD

        return Response({
            'period_days': days,
            'threshold': self.ALERT_THRESHOLD,
            'results': results,
        })
