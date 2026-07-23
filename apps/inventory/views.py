from datetime import date, timedelta

from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema
from rest_framework import generics
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

    search_fields = ['name_uz', 'name_iupac', 'cas_number', 'formula']
    ordering_fields = ['name_uz', 'expiry_date', 'quantity']

    def get_queryset(self):
        qs = Chemical.objects.all()
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is None:
            return qs.filter(is_active=True)
        if is_active_param.lower() in ('false', '0'):
            return qs.filter(is_active=False)
        return qs.filter(is_active=True)


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
    """
       Miqdorni oshirish/kamaytirish — bir vaqtda bir nechta so'rov kelsa ham
       xavfsiz bo'lishi uchun qator bazada bloklanadi (select_for_update),
       shu sababli tekshiruv har doim eng so'nggi (haqiqiy) miqdorga nisbatan bajariladi.
       """
    permission_classes = [IsChemist]
    serializer_class = ChemicalQuantitySerializer

    @transaction.atomic
    def patch(self, request, pk):
        chemical = generics.get_object_or_404(Chemical.objects.select_for_update(), pk=pk)
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
        chemical.save(update_fields=['quantity'])

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
            'expired': ChemicalAlertSerializer(expired, many=True).data,
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


@extend_schema(tags=['Chemicals'])
class ChemicalActivateView(APIView):
    """ Faolsizlantirilgan reaktivni qayta faollashtirish. PATCH /chemicals/<id>/activate/ """
    permission_classes = [IsAdmin]
    serializer_class = ChemicalDetailSerializer

    def patch(self, request, pk):
        chemical = generics.get_object_or_404(Chemical, pk=pk)
        chemical.is_active = True
        chemical.save()
        return Response({'message': f"{chemical.name_uz} qayta faollashtirildi."})
