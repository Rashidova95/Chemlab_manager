from decimal import Decimal

from rest_framework import serializers

from .models import Chemical


class ChemicalListSerializer(serializers.ModelSerializer):
    """
    ET /api/v1/chemicals/
    """
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Chemical
        fields = [
            'id', 'name_uz', 'formula', 'cas_number',
            'quantity', 'unit', 'hazard_level', 'expiry_date',
            'is_active', 'is_low_stock', 'is_expiring_soon', 'is_expired',
        ]


class ChemicalDetailSerializer(serializers.ModelSerializer):
    """
    GET /api/v1/chemicals/{id}/
    """
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)


    class Meta:
        model = Chemical
        fields = [
            'id', 'name_uz', 'name_iupac', 'formula', 'cas_number',
            'quantity', 'unit', 'min_threshold',
            'expiry_date', 'hazard_level',
            'supplier', 'storage_condition', 'is_active',
            'is_low_stock', 'is_expiring_soon', 'is_expired',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ChemicalCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/v1/chemicals/create/
    """

    class Meta:
        model = Chemical
        fields = [
            'name_uz', 'name_iupac', 'formula', 'cas_number',
            'quantity', 'unit', 'min_threshold',
            'expiry_date', 'hazard_level',
            'supplier', 'storage_condition',
        ]


class ChemicalAlertSerializer(serializers.ModelSerializer):
    """
   GET /api/v1/chemicals/alerts/
    """
    is_low_stock = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)


    class Meta:
        model = Chemical
        fields = [
            'id', 'name_uz', 'formula',
            'quantity', 'unit', 'min_threshold', 'expiry_date',
            'is_expiring_soon', 'is_low_stock', 'is_expired',
        ]


class ChemicalQuantitySerializer(serializers.Serializer):
    """
    PATCH /api/v1/chemicals/{id}/quantity/
    """
    ACTION_CHOICES = ['add', 'subtract']
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        min_value=Decimal('0.01')
    )

    def validate(self, data):
        chemical = self.context['chemical']
        if data['action'] == 'subtract' and data['amount'] > chemical.quantity:
            raise serializers.ValidationError(
                f"Yetarli miqdor yo'q. Mavjud: {chemical.quantity}"
            )
        return data
