from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """ Yangi foydalanuvchi yaratish."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Parollar mos kelmadi.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """ Email + parol validatsiyasi."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Email yoki parol noto'g'ri.")

        if not user.is_active:
            raise serializers.ValidationError("Foydalanuvchi bloklangan.")

        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """ Rol va profil ma'lumotlari."""
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['email', 'role', 'lab_name', 'phone', 'is_active']
        read_only_fields = ['email', 'role', 'is_active']


class UserSerializer(serializers.ModelSerializer):
    """ Foydalanuvchi ma'lumotlari + profil."""
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'profile']
        read_only_fields = ['id', 'email']

    def update(self, instance, validated_data):

        profile_data = validated_data.pop('profile', {})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Profileni yangilaymiz
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """ Parol o'zgartirish validatsiyasi."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri.")
        return value

class AdminUserListSerializer(serializers.ModelSerializer):
    """ Admin uchun — foydalanuvchilar ro'yxati (rol boshqaruvi sahifasi)."""
    role = serializers.CharField(source='profile.role')
    lab_name = serializers.CharField(source='profile.lab_name')
    phone = serializers.CharField(source='profile.phone')
    is_active_profile = serializers.BooleanField(source='profile.is_active')

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'lab_name', 'phone', 'is_active_profile',
            'is_active', 'date_joined',
        ]
        read_only_fields = fields


class AdminUserRoleUpdateSerializer(serializers.Serializer):
    """ Admin — boshqa foydalanuvchining rolini/holatini o'zgartiradi."""
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Kamida bitta maydon (role yoki is_active) yuborilishi kerak.")
        return data


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """ Admin uchun — yangi foydalanuvchi yaratish, rolni darhol belgilash."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True, required=False)
    lab_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'role', 'lab_name', 'phone']

    def create(self, validated_data):
        role = validated_data.pop('role', 'viewer')
        lab_name = validated_data.pop('lab_name', '')
        phone = validated_data.pop('phone', '')

        user = User.objects.create_user(**validated_data)
        user.profile.role = role
        user.profile.lab_name = lab_name
        user.profile.phone = phone
        user.profile.save()
        return user

    def to_representation(self, instance):
        return AdminUserListSerializer(instance).data
