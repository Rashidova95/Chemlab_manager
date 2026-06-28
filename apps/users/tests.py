from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CustomUser, UserProfile


# -----------------------------------------------
# 1. MODEL TESTLAR
# -----------------------------------------------
class UserModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@lab.uz',
            username='test',
            password='Test1234!'
        )

    def test_user_yaratildi(self):
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_email_login(self):
        self.assertEqual(self.user.email, 'test@lab.uz')

    def test_profil_avtomatik_yaratildi(self):
        # Signal ishlashi kerak
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.role, 'viewer')

    def test_rol_helperlari(self):
        profile = self.user.profile
        self.assertFalse(profile.is_admin())
        self.assertFalse(profile.is_chemist())
        self.assertTrue(profile.is_viewer())


# -----------------------------------------------
# 2. REGISTER TESTLAR
# -----------------------------------------------
class RegisterTest(APITestCase):

    def setUp(self):
        self.url = reverse('auth-register')
        self.data = {
            'email':      'ali@lab.uz',
            'username':   'ali',
            'first_name': 'Ali',
            'last_name':  'Valiyev',
            'password':   'Test1234!',
            'password2':  'Test1234!',
        }

    def test_register_ishlaydi(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_parollar_mos_kelmasa(self):
        self.data['password2'] = 'BoshqaParol!'
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_takrorlanmaydi(self):
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_qisqa_parol(self):
        self.data['password'] = '123'
        self.data['password2'] = '123'
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------
# 3. LOGIN TESTLAR
# -----------------------------------------------
class LoginTest(APITestCase):

    def setUp(self):
        self.url = reverse('auth-login')
        self.user = CustomUser.objects.create_user(
            email='ali@lab.uz',
            username='ali',
            password='Test1234!'
        )

    def test_login_ishlaydi(self):
        response = self.client.post(self.url, {
            'email':    'ali@lab.uz',
            'password': 'Test1234!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_notogri_parol(self):
        response = self.client.post(self.url, {
            'email':    'ali@lab.uz',
            'password': 'XatoParol!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notogri_email(self):
        response = self.client.post(self.url, {
            'email':    'yoq@lab.uz',
            'password': 'Test1234!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------
# 4. ME ENDPOINT TESTLAR
# -----------------------------------------------
class MeTest(APITestCase):

    def setUp(self):
        self.url = reverse('auth-me')
        self.user = CustomUser.objects.create_user(
            email='ali@lab.uz',
            username='ali',
            first_name='Ali',
            password='Test1234!'
        )
        # Login qilib token olamiz
        self.client.force_authenticate(user=self.user)

    def test_profil_korish(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'ali@lab.uz')

    def test_profil_tahrirlash(self):
        response = self.client.patch(self.url, {
            'first_name': 'Alibek',
            'profile': {'lab_name': 'Kimyo lab'}
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alibek')

    def test_token_siz_403(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# -----------------------------------------------
# 5. PAROL O'ZGARTIRISH TESTLAR
# -----------------------------------------------
class ChangePasswordTest(APITestCase):

    def setUp(self):
        self.url = reverse('auth-change-password')
        self.user = CustomUser.objects.create_user(
            email='ali@lab.uz',
            username='ali',
            password='Test1234!'
        )
        self.client.force_authenticate(user=self.user)

    def test_parol_ozgartirildi(self):
        response = self.client.post(self.url, {
            'old_password': 'Test1234!',
            'new_password': 'Yangi1234!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Yangi parol ishlayaptimi
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Yangi1234!'))

    def test_eski_parol_xato(self):
        response = self.client.post(self.url, {
            'old_password': 'XatoParol!',
            'new_password': 'Yangi1234!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
