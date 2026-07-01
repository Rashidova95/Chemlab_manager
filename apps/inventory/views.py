from datetime import date, timedelta

from django.db.models import F
from drf_spectacular.utils import extend_schema
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin, IsChemist
from .models import Chemical
from .serializers import (
    ChemicalListSerializer,
    ChemicalDetailSerializer,
    ChemicalCreateSerializer,
    ChemicalAlertSerializer,
    ChemicalQuantitySerializer,
)


@extend_schema(tags=['Chemicals'])
class ChemicalListView(generics.ListAPIView):
    """
    Reaktivlar ro'yxati — hammaga.
    GET /api/v1/chemicals/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChemicalListSerializer

    queryset = Chemical.objects.filter(is_active=True)
    search_fields = ['name_uz', 'name_iupac', 'cas_number', 'formula']
    ordering_fields = ['name_uz', 'expiry_date', 'quantity']


@extend_schema(tags=['Chemicals'])
class ChemicalCreateView(generics.CreateAPIView):
    """
    Yangi reaktiv qo'shish — faqat admin.
    POST /api/v1/chemicals/
    """
    permission_classes = [IsAdmin]
    serializer_class = ChemicalCreateSerializer


@extend_schema(tags=['Chemicals'])
class ChemicalDetailView(generics.RetrieveAPIView):
    """
    Reaktiv detallari — hammaga.
    GET /api/v1/chemicals/{id}/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChemicalDetailSerializer
    queryset = Chemical.objects.all()


@extend_schema(tags=['Chemicals'])
class ChemicalUpdateView(generics.UpdateAPIView):
    """
    Reaktivni tahrirlash — faqat admin.
    PUT/PATCH /api/v1/chemicals/{id}/
    """
    permission_classes = [IsAdmin]
    serializer_class = ChemicalCreateSerializer
    queryset = Chemical.objects.all()
    http_method_names = ['patch']


@extend_schema(tags=['Chemicals'])
class ChemicalUpdateQuantityView(APIView):
    permission_classes = [IsChemist]
    serializer_class = ChemicalQuantitySerializer

    def patch(self, request, pk):
        chemical = generics.get_object_or_404(Chemical, pk=pk)
        serializer = ChemicalQuantitySerializer(
            data=request.data,
            context={'chemical': chemical}
        )
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        amount = serializer.validated_data['amount']

        if action == 'add':
            chemical.quantity += amount
        else:
            chemical.quantity -= amount
        chemical.save()

        return Response({
            'message': f"{action} — {amount} {chemical.unit}",
            'new_quantity': chemical.quantity,
        })


@extend_schema(tags=['Chemicals'])
class ChemicalAlertView(APIView):
    """
    Ogohlantirishlar — kam qolgan va muddati tugayotgan.
    GET /api/v1/chemicals/alerts/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChemicalAlertSerializer

    def get(self, request):
        today = date.today()
        soon = today + timedelta(days=30)

        low_stock = Chemical.objects.filter(is_active=True, quantity__lte=F('min_threshold'))
        expiring_soon = Chemical.objects.filter(is_active=True, expiry_date__gte=today, expiry_date__lte=soon)
        expired = Chemical.objects.filter(is_active=True, expiry_date__lt=today)

        return Response({
            'low_stock': ChemicalAlertSerializer(low_stock, many=True).data,
            'expiring_soon': ChemicalAlertSerializer(expiring_soon, many=True).data,
            'expired': ChemicalAlertSerializer(expired, many=True).data,  # + yangi
        })


@extend_schema(tags=['Chemicals'])
class ChemicalDeactivateView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = ChemicalDetailSerializer

    def patch(self, request, pk):
        chemical = generics.get_object_or_404(Chemical, pk=pk)
        chemical.is_active = False
        chemical.save()
        return Response({'message': f"{chemical.name_uz} arxivlandi."})
