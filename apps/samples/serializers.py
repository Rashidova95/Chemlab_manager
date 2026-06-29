from rest_framework import serializers

from .models import Sample, SampleStatusLog


class SampleStatusLogSerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()

    class Meta:
        model = SampleStatusLog
        fields = ['old_status', 'new_status', 'changed_by', 'changed_at']


class SampleListSerializer(serializers.ModelSerializer):
    received_by = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = [
            'id', 'sample_id', 'name', 'source_type',
            'status', 'quantity', 'unit',
            'received_by', 'received_at',
        ]

    def get_received_by(self, obj):
        if obj.received_by:
            return {
                'email': obj.received_by.email,
                'name': obj.received_by.get_full_name(),
            }
        return None


class SampleDetailSerializer(serializers.ModelSerializer):
    received_by = serializers.SerializerMethodField()
    logs = SampleStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model = Sample
        fields = [
            'id', 'sample_id', 'name', 'source_type',
            'status', 'quantity', 'unit', 'notes',
            'received_by', 'received_at', 'updated_at', 'logs',
        ]
        read_only_fields = ['sample_id', 'received_at', 'updated_at']

    def get_received_by(self, obj):
        if obj.received_by:
            return {
                'email': obj.received_by.email,
                'name': obj.received_by.get_full_name(),
            }
        return None


class SampleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ['name', 'source_type', 'quantity', 'unit', 'notes']

    def create(self, validated_data):
        validated_data['received_by'] = self.context['request'].user
        return super().create(validated_data)


class SampleStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ['status']

    def validate_status(self, new_status):
        if not self.instance.can_move_to(new_status):
            raise serializers.ValidationError(
                f"'{self.instance.status}' dan '{new_status}' ga o'tib bo'lmaydi."
            )
        return new_status
