from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsLaborant, IsChemist
from .models import Experiment
from .serializers import (
    ExperimentListSerializer,
    ExperimentDetailSerializer,
    ExperimentCreateSerializer,
    ExperimentUpdateSerializer,
    ExperimentApproveSerializer,
    ExperimentRejectSerializer,
)


@extend_schema(tags=['Experiments'])
class ExperimentListView(generics.ListAPIView):
    """Ro'yxat — hammaga."""
    permission_classes = [IsAuthenticated]
    serializer_class = ExperimentListSerializer
    search_fields = ['title', 'sample__sample_id']
    ordering_fields = ['created_at', 'status']

    def get_queryset(self):
        qs = Experiment.objects.select_related('sample', 'performed_by')

        # Status filtri
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)

        # Sample filtri
        sample_id = self.request.query_params.get('sample')
        if sample_id:
            qs = qs.filter(sample_id=sample_id)

        return qs


@extend_schema(tags=['Experiments'])
class ExperimentCreateView(generics.CreateAPIView):
    """Yangi tajriba — laborant va yuqori."""
    permission_classes = [IsLaborant]
    serializer_class = ExperimentCreateSerializer


@extend_schema(tags=['Experiments'])
class ExperimentDetailView(generics.RetrieveAPIView):
    """To'liq ma'lumot — hammaga."""
    permission_classes = [IsAuthenticated]
    serializer_class = ExperimentDetailSerializer
    queryset = Experiment.objects.select_related(
        'sample', 'performed_by', 'approved_by'
    ).prefetch_related('chemicals_used')


@extend_schema(tags=['Experiments'])
class ExperimentUpdateView(generics.UpdateAPIView):
    """Tahrirlash — faqat bajargan laborant."""
    permission_classes = [IsLaborant]
    serializer_class = ExperimentUpdateSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return Experiment.objects.filter(performed_by=self.request.user)


@extend_schema(tags=['Experiments'])
class ExperimentApproveView(APIView):
    """Tasdiqlash — faqat chemist va admin."""
    permission_classes = [IsChemist]
    serializer_class = ExperimentApproveSerializer

    def patch(self, request, pk):
        experiment = generics.get_object_or_404(Experiment, pk=pk)
        serializer = ExperimentApproveSerializer(
            experiment,
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ExperimentDetailSerializer(experiment).data)


@extend_schema(tags=['Experiments'])
class ExperimentRejectView(APIView):
    """Qaytarish — faqat chemist va admin."""
    permission_classes = [IsChemist]
    serializer_class = ExperimentRejectSerializer

    def patch(self, request, pk):
        experiment = generics.get_object_or_404(Experiment, pk=pk)
        serializer = ExperimentRejectSerializer(
            experiment,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ExperimentDetailSerializer(experiment).data)
