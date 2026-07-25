from rest_framework import serializers


class ChatMessageInSerializer(serializers.Serializer):
    """ Foydalanuvchidan kelgan xabar + (ixtiyoriy) suhbat tarixi."""
    message = serializers.CharField(max_length=2000)
    history = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class ChatMessageOutSerializer(serializers.Serializer):
    reply = serializers.CharField()
