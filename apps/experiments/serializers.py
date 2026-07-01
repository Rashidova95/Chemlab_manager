from django.utils import timezone
from rest_framework import serializers

from .models import Experiment


class ExperimentListSerializer(serializers.ModelSerializer):
    """GET /experiments/ — ro'yxat uchun."""
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name',
        read_only=True
    )
    sample_id = serializers.CharField(
        source='sample.sample_id',
        read_only=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Experiment
        fields = [
            'id', 'title', 'sample', 'sample_id',
            'status', 'performed_by_name', 'created_at',
        ]


class ExperimentDetailSerializer(serializers.ModelSerializer):
    """GET /experiments/{id}/ — to'liq ma'lumot."""
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name',
        read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.get_full_name',
        read_only=True,
        default=None
    )
    sample_id = serializers.CharField(source='sample.sample_id', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    approved_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", allow_null=True)

    class Meta:
        model = Experiment
        fields = [
            'id', 'sample', 'sample_id', 'title', 'method',
            'objective', 'observations', 'results',
            'status', 'rejection_reason',
            'performed_by', 'performed_by_name',
            'approved_by', 'approved_by_name', 'approved_at',
            'chemicals_used', 'attachment',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'performed_by', 'approved_by',
            'approved_at', 'created_at', 'updated_at',
        ]


class ExperimentCreateSerializer(serializers.ModelSerializer):
    """POST /experiments/ — yangi tajriba yaratish."""

    class Meta:
        model = Experiment
        fields = [
            'sample', 'title', 'method', 'objective',
            'observations', 'results', 'chemicals_used', 'attachment',
        ]

    def create(self, validated_data):
        validated_data['performed_by'] = self.context['request'].user
        return super().create(validated_data)


class ExperimentUpdateSerializer(serializers.ModelSerializer):
    """PATCH /experiments/{id}/ — tahrirlash."""

    class Meta:
        model = Experiment
        fields = [
            'title', 'method', 'objective',
            'observations', 'results',
            'chemicals_used', 'attachment', 'status',
        ]

    def validate(self, attrs):
        # Approved tajribani tahrirlashni bloklash
        if self.instance and self.instance.status == 'approved':
            raise serializers.ValidationError(
                "Approved tajribani tahrirlash mumkin emas."
            )
        return attrs

    def validate_status(self, new_status):
        instance = self.instance
        if not instance.can_move_to(new_status):
            raise serializers.ValidationError(
                f"'{instance.get_status_display()}' dan "
                f"'{new_status}' ga o'tib bo'lmaydi."
            )
        return new_status


class ExperimentApproveSerializer(serializers.ModelSerializer):
    """PATCH /experiments/{id}/approve/ — tasdiqlash."""

    class Meta:
        model = Experiment
        fields = ['status']

    def validate(self, data):
        if self.instance.status != 'review':
            raise serializers.ValidationError(
                "Faqat 'Tekshiruvda' holatidagi tajribani tasdiqlash mumkin."
            )
        return data

    def update(self, instance, validated_data):
        instance.status = 'approved'
        instance.approved_by = self.context['request'].user
        instance.approved_at = timezone.now()
        instance.save()
        return instance


class ExperimentRejectSerializer(serializers.ModelSerializer):
    """PATCH /experiments/{id}/reject/ — qaytarish."""
    rejection_reason = serializers.CharField(required=True, min_length=10)

    class Meta:
        model = Experiment
        fields = ['rejection_reason']

    def validate(self, data):
        if self.instance.status != 'review':
            raise serializers.ValidationError(
                "Faqat 'Tekshiruvda' holatidagi tajribani qaytarish mumkin."
            )
        return data

    def update(self, instance, validated_data):
        instance.status = 'rejected'
        instance.rejection_reason = validated_data['rejection_reason']
        instance.save()
        return instance
