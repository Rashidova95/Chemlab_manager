import csv

from django.db import transaction, connection
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsLaborant
from .models import Sample, SampleStatusLog
from .serializers import (
    SampleListSerializer,
    SampleDetailSerializer,
    SampleCreateSerializer,
    SampleStatusSerializer,
)


@extend_schema(tags=['Samples'])
class SampleListView(generics.ListAPIView):
    """ Namunalar ro'yxati."""
    permission_classes = [IsAuthenticated]
    serializer_class = SampleListSerializer
    queryset = Sample.objects.select_related('received_by').all()
    search_fields = ['sample_id', 'name']
    ordering_fields = ['received_at', 'status', 'name']
    filterset_fields = ['status', 'source_type']


@extend_schema(tags=['Samples'])
class SampleCreateView(generics.CreateAPIView):
    """Yangi namuna qabul qilish."""
    permission_classes = [IsLaborant]
    serializer_class = SampleCreateSerializer

    def perform_create(self, serializer):
        # Bir vaqtda bir nechta laborant namuna qo'shsa ham bir xil sample_id
        # (masalan ikkalasiga ham CHEM-2026-00006) berilib qolmasligi uchun,
        # shu yil bo'yicha PostgreSQL advisory lock bilan navbatga solamiz.
        # Lock tranzaksiya tugagach (COMMIT/ROLLBACK) avtomatik yechiladi.
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [timezone.now().year])
            serializer.save()


@extend_schema(tags=['Samples'])
class SampleDetailView(generics.RetrieveAPIView):
    """Namuna detallari."""
    permission_classes = [IsAuthenticated]
    serializer_class = SampleDetailSerializer
    queryset = Sample.objects.select_related('received_by').prefetch_related('logs')


@extend_schema(tags=['Samples'])
class SampleStatusUpdateView(APIView):
    """Status yangilash."""
    permission_classes = [IsLaborant]
    serializer_class = SampleStatusSerializer

    def patch(self, request, pk):
        sample = generics.get_object_or_404(Sample, pk=pk)
        old_status = sample.status

        serializer = SampleStatusSerializer(sample, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        SampleStatusLog.objects.create(
            sample=sample,
            old_status=old_status,
            new_status=sample.status,
            changed_by=request.user,
        )

        return Response(SampleDetailSerializer(sample).data)


@extend_schema(tags=['Samples'])
class SampleCSVExportView(APIView):
    """ CSV eksport."""
    permission_classes = [IsAuthenticated]
    serializer_class = SampleListSerializer

    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="samples.csv"'

        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response, delimiter=',')
        writer.writerow(['ID', 'Nomi', 'Manba', 'Holat', 'Miqdor', 'Birlik', 'Sana'])

        for s in Sample.objects.select_related('received_by'):
            writer.writerow([
                s.sample_id,
                s.name,
                s.get_source_type_display(),
                s.get_status_display(),
                s.quantity,
                s.unit,
                localtime(s.received_at).strftime('%Y-%m-%d %H:%M'),
            ])

        return response
