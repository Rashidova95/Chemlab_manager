from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Sample, SampleStatusLog


class SampleStatusLogSerializer(serializers.ModelSerializer):
    """ Status o'zgarish tarixi."""
    changed_by = serializers.StringRelatedField()
    changed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = SampleStatusLog
        fields = ['old_status', 'new_status', 'changed_by', 'changed_at']


class SampleListSerializer(serializers.ModelSerializer):
    """ Namunalar ro'yxati """
    received_by = serializers.SerializerMethodField()
    received_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Sample
        fields = [
            'id', 'sample_id', 'name', 'source_type',
            'status', 'quantity', 'unit',
            'received_by', 'received_at',
        ]

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
            'name': {'type': 'string'},
        }
    })
    def get_received_by(self, obj):
        if obj.received_by:
            return {
                'email': obj.received_by.email,
                'name': obj.received_by.get_full_name(),
            }
        return None


class SampleDetailSerializer(serializers.ModelSerializer):
    """ Namuna detali — status tarixi bilan."""
    received_by = serializers.SerializerMethodField()
    received_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    logs = SampleStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = [
            'id', 'sample_id', 'name', 'source_type',
            'status', 'quantity', 'unit', 'notes',
            'received_by', 'received_at', 'updated_at', 'logs',
        ]
        read_only_fields = ['sample_id', 'received_at', 'updated_at']

    @extend_schema_field({
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
            'name': {'type': 'string'},
        }
    })
    def get_received_by(self, obj):
        if obj.received_by:
            return {
                'email': obj.received_by.email,
                'name': obj.received_by.get_full_name(),
            }
        return None


class SampleCreateSerializer(serializers.ModelSerializer):
    """ Yangi namuna yaratish — received_by tokendan."""
    class Meta:
        model = Sample
        fields = ['name', 'source_type', 'quantity', 'unit', 'notes']

    def create(self, validated_data):
        validated_data['received_by'] = self.context['request'].user
        return super().create(validated_data)


class SampleStatusSerializer(serializers.ModelSerializer):
    """ Status yangilash — can_move_to tekshiradi."""
    class Meta:
        model = Sample
        fields = ['status']

    def validate_status(self, new_status):
        if not self.instance.can_move_to(new_status):
            raise serializers.ValidationError(
                f"'{self.instance.status}' dan '{new_status}' ga o'tib bo'lmaydi."
            )
        return new_status
