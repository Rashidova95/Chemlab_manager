from django.conf import settings
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.experiments.models import Experiment
from apps.inventory.models import Chemical
from apps.samples.models import Sample
from .serializers import ChatMessageInSerializer, ChatMessageOutSerializer

MAX_HISTORY_MESSAGES = 10


def build_lab_context():
    """
    Tizimdagi joriy holatning qisqa xulosasini tayyorlaydi — bu AI'ga
    "hozir nechta namuna kutilmoqda", "qaysi reaktivlar kam qoldi" kabi
    savollarga haqiqiy ma'lumot asosida javob berish imkonini beradi.
    """
    samples_total = Sample.objects.count()
    samples_by_status = {
        row['status']: row['count']
        for row in Sample.objects.values('status').annotate(count=Count('id'))
    }

    experiments_pending = Experiment.objects.filter(status='review').count()

    active_chemicals = Chemical.objects.filter(is_active=True)
    low_stock = [c.name_uz for c in active_chemicals if c.is_low_stock][:15]
    expiring = [c.name_uz for c in active_chemicals if c.is_expiring_soon][:15]
    expired = [c.name_uz for c in active_chemicals if c.is_expired][:15]

    none_label = 'yoq'
    return (
        f"Jami namunalar: {samples_total}. Holat bo'yicha: {samples_by_status}.\n"
        f"Tekshiruvni kutayotgan tajribalar: {experiments_pending}.\n"
        f"Kam qolgan reaktivlar: {', '.join(low_stock) or none_label}.\n"
        f"Muddati tugayotgan reaktivlar: {', '.join(expiring) or none_label}.\n"
        f"Muddati tugagan reaktivlar: {', '.join(expired) or none_label}."
    )


@extend_schema(tags=['Assistant'], request=ChatMessageInSerializer, responses={200: ChatMessageOutSerializer})
class AssistantChatView(APIView):
    """
    Umumiy AI yordamchi — laboratoriya ma'lumotlari asosida savollarga
    javob beradi (statistika, reaktiv holati va h.k.). Faqat o'qish uchun —
    hech qanday amalni (yaratish/o'zgartirish) bajarmaydi.

    POST /api/v1/assistant/chat/
    Body: { "message": "...", "history": [{"role": "user"|"assistant", "content": "..."}] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatMessageInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return Response(
                {'detail': "AI yordamchi sozlanmagan — administrator GEMINI_API_KEY ni .env ga qo'shishi kerak."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return Response(
                {'detail': "'google-genai' kutubxonasi o'rnatilmagan (requirements.txt ga qarang)."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        user = request.user
        role = getattr(user.profile, 'role', 'viewer') if hasattr(user, 'profile') else 'viewer'

        system_prompt = (
            "Sen ChemLab UZ — kimyo laboratoriyasi boshqaruv tizimining AI yordamchisisan. "
            "Faqat o'zbek tilida, qisqa va aniq javob ber. Foydalanuvchi roli: "
            f"{role}. Quyida tizimning joriy holati (haqiqiy ma'lumotlar) berilgan — "
            "javoblaringizni shularga asoslang, o'zingizdan raqam to'qimang:\n\n"
            f"{build_lab_context()}\n\n"
            "Agar savol tizim ma'lumotlariga aloqador bo'lmasa (masalan umumiy kimyo "
            "savoli), oddiy bilimga tayanib javob berishing mumkin. Agar foydalanuvchi "
            "biror amalni (o'chirish, yaratish) so'rasa, buni o'zing bajara olmasligingni "
            "va tegishli sahifadan foydalanish kerakligini ayt."
        )

        history = serializer.validated_data.get('history', [])[-MAX_HISTORY_MESSAGES:]
        # Gemini rollarni 'user' / 'model' deb ataydi ('assistant' emas)
        contents = [
            {
                'role': 'model' if m.get('role') == 'assistant' else 'user',
                'parts': [{'text': m.get('content')}],
            }
            for m in history
            if m.get('role') in ('user', 'assistant') and m.get('content')
        ]
        contents.append({'role': 'user', 'parts': [{'text': serializer.validated_data['message']}]})

        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash'),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=800,
                ),
            )
        except Exception as exc:
            return Response(
                {'detail': f"AI yordamchidan javob olib bo'lmadi: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        reply_text = response.text or "Kechirasiz, javob bera olmadim."

        return Response(ChatMessageOutSerializer({'reply': reply_text}).data)
