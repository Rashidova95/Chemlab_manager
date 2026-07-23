from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    AdminUserListSerializer,
    AdminUserRoleUpdateSerializer,
    AdminUserCreateSerializer,
)

User = get_user_model()


@extend_schema(tags=['Auth'])
class RegisterView(generics.CreateAPIView):
    """ Yangi foydalanuvchi ro'yxatdan o'tishi. POST /api/v1/auth/register/ """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@extend_schema(tags=['Auth'])
class LoginView(APIView):
    """ Email + parol bilan kirish, JWT token olish. POST /api/v1/auth/login/"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


@extend_schema(tags=['Auth'])
class MeView(generics.RetrieveUpdateAPIView):
    """ O'z profilini ko'rish va tahrirlash. GET/PATCH /api/v1/auth/me/"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch']

    def get_object(self):
        return self.request.user

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            self.get_object(),
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(tags=['Auth'])
class ChangePasswordView(APIView):
    """ Parol o'zgartirish. POST /api/v1/auth/change-password/"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    @extend_schema(request=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({'message': "Parol muvaffaqiyatli o'zgartirildi."})


@extend_schema(tags=['Users (Admin)'])
class AdminUserListView(generics.ListAPIView):
    """ Barcha foydalanuvchilar ro'yxati (faqat admin). GET /api/v1/auth/users/ """
    queryset = User.objects.select_related('profile').order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'email']


@extend_schema(tags=['Users (Admin)'])
class AdminUserRoleUpdateView(APIView):
    """
    Foydalanuvchining rolini yoki faollik holatini o'zgartiradi (faqat admin).
    PATCH /api/v1/auth/users/<id>/role/
    Body: { "role": "chemist" } va/yoki { "is_active": false }
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminUserRoleUpdateSerializer

    @extend_schema(request=AdminUserRoleUpdateSerializer)
    def patch(self, request, pk):
        try:
            target_user = User.objects.select_related('profile').get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Foydalanuvchi topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

        if target_user.id == request.user.id:
            return Response(
                {'detail': "O'zingizning rolingizni/holatingizni shu yerdan o'zgartira olmaysiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminUserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if 'role' in serializer.validated_data:
            target_user.profile.role = serializer.validated_data['role']
        if 'is_active' in serializer.validated_data:
            target_user.profile.is_active = serializer.validated_data['is_active']
            # CustomUser.is_active bilan ham sinxronlaymiz — bloklangan foydalanuvchi tizimga kira olmasin
            target_user.is_active = serializer.validated_data['is_active']
            target_user.save(update_fields=['is_active'])

        target_user.profile.save()

        return Response(AdminUserListSerializer(target_user).data)


@extend_schema(tags=['Users (Admin)'])
class AdminUserCreateView(generics.CreateAPIView):
    """
    Admin tomonidan yangi foydalanuvchi yaratish — rolni darhol belgilab
    (odatiy ro'yxatdan o'tishdan farqli, u yerda rol har doim 'viewer').
    POST /api/v1/auth/users/create/
    """
    queryset = User.objects.all()
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


@extend_schema(tags=['Users (Admin)'])
class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Bitta foydalanuvchini ko'rish, profil ma'lumotlarini (ism, familiya,
    laboratoriya, telefon) tahrirlash yoki o'chirish (faqat admin).
    GET / PATCH / DELETE /api/v1/auth/users/<id>/
    (Rol va faollik holati uchun /users/<id>/role/ dan foydalaning.)
    """
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ['get', 'patch', 'delete']

    def perform_destroy(self, instance):
        if instance.id == self.request.user.id:
            raise ValidationError("O'zingizni o'chira olmaysiz.")

        from apps.samples.models import Sample
        from apps.experiments.models import Experiment

        has_history = (
                Sample.objects.filter(received_by=instance).exists()
                or Experiment.objects.filter(performed_by=instance).exists()
                or Experiment.objects.filter(approved_by=instance).exists()
        )
        if has_history:
            raise ValidationError(
                "Bu foydalanuvchi nomidan namuna/tajriba qo'shilgan — audit tarixini "
                "saqlab qolish uchun uni o'chirib bo'lmaydi. Buning o'rniga faolsizlantiring."
            )

        instance.delete()
