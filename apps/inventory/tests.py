from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Chemical

User = get_user_model()


# -----------------------------------------------
# YORDAMCHI
# -----------------------------------------------
def make_chemical(**kwargs):
    defaults = {
        'name_uz': 'Sulfat kislota',
        'name_iupac': 'Sulfuric acid',
        'cas_number': '7664-93-9',
        'formula': 'H2SO4',
        'quantity': Decimal('500'),
        'unit': 'ml',
        'min_threshold': Decimal('50'),
        'expiry_date': date.today() + timedelta(days=60),
        'hazard_level': 3,
    }
    defaults.update(kwargs)
    return Chemical.objects.create(**defaults)


class ChemicalBaseTest(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@lab.uz', username='admin', password='Test1234!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.laborant = User.objects.create_user(
            email='laborant@lab.uz', username='laborant', password='Test1234!'
        )

        self.chemical = make_chemical()

    def as_admin(self):
        self.client.force_authenticate(user=self.admin)

    def as_laborant(self):
        self.client.force_authenticate(user=self.laborant)


# -----------------------------------------------
# 1. RO'YXAT — ChemicalListSerializer
# -----------------------------------------------
class ChemicalListTest(ChemicalBaseTest):

    def test_royxat_200(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-list'))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_royxatda_detail_maydonlar_yoq(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-list'))
        item = r.data['results'][0]
        self.assertNotIn('created_at', item)
        self.assertNotIn('updated_at', item)
        self.assertNotIn('storage_condition', item)
        self.assertNotIn('supplier', item)

    def test_royxatda_asosiy_maydonlar_bor(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-list'))
        item = r.data['results'][0]
        self.assertIn('id', item)
        self.assertIn('name_uz', item)
        self.assertIn('quantity', item)
        self.assertIn('is_low_stock', item)

    def test_qidiruv_ishlaydi(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-list'), {'search': 'Sulfat'})
        self.assertEqual(r.data['count'], 1)

    def test_token_siz_401(self):
        r = self.client.get(reverse('chemical-list'))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_arxivlangan_korinmaydi(self):
        self.chemical.is_active = False
        self.chemical.save()
        self.as_laborant()
        r = self.client.get(reverse('chemical-list'))
        self.assertEqual(r.data['count'], 0)


# -----------------------------------------------
# 2. YARATISH — ChemicalCreateSerializer
# -----------------------------------------------
class ChemicalCreateTest(ChemicalBaseTest):

    def get_data(self, **kwargs):
        data = {
            'name_uz': 'Xlorid kislota',
            'name_iupac': 'Hydrochloric acid',
            'formula': 'HCl',
            'cas_number': '7647-01-0',
            'quantity': 200,
            'unit': 'ml',
            'min_threshold': 30,
            'expiry_date': str(date.today() + timedelta(days=90)),
            'hazard_level': 2,
        }
        data.update(kwargs)
        return data

    def test_admin_yarata_oladi(self):
        self.as_admin()
        r = self.client.post(reverse('chemical-create'), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_laborant_yarata_olmaydi(self):
        self.as_laborant()
        r = self.client.post(reverse('chemical-create'), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_cas_takrorlanmaydi(self):
        self.as_admin()
        r = self.client.post(reverse('chemical-create'), self.get_data(cas_number='7664-93-9'))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_javobda_created_at_yoq(self):
        self.as_admin()
        r = self.client.post(reverse('chemical-create'), self.get_data())
        self.assertNotIn('created_at', r.data)


# -----------------------------------------------
# 3. DETAIL — ChemicalDetailSerializer
# -----------------------------------------------
class ChemicalDetailTest(ChemicalBaseTest):

    def test_detail_200(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-detail', args=[self.chemical.pk]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_barcha_maydonlar_bor(self):
        self.as_laborant()
        r = self.client.get(reverse('chemical-detail', args=[self.chemical.pk]))
        self.assertIn('created_at', r.data)
        self.assertIn('updated_at', r.data)
        self.assertIn('storage_condition', r.data)
        self.assertIn('supplier', r.data)
        self.assertIn('is_expired', r.data)


# -----------------------------------------------
# 4. MIQDOR — ChemicalQuantitySerializer
# -----------------------------------------------
class ChemicalQuantityTest(ChemicalBaseTest):

    def test_add_ishlaydi(self):
        self.as_admin()
        r = self.client.patch(
            reverse('chemical-quantity', args=[self.chemical.pk]),
            {'action': 'add', 'amount': '100'}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.chemical.refresh_from_db()
        self.assertEqual(self.chemical.quantity, Decimal('600'))

    def test_subtract_ishlaydi(self):
        self.as_admin()
        r = self.client.patch(
            reverse('chemical-quantity', args=[self.chemical.pk]),
            {'action': 'subtract', 'amount': '100'}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.chemical.refresh_from_db()
        self.assertEqual(self.chemical.quantity, Decimal('400'))

    def test_yetarli_miqdor_yoq(self):
        self.as_admin()
        r = self.client.patch(
            reverse('chemical-quantity', args=[self.chemical.pk]),
            {'action': 'subtract', 'amount': '9999'}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_laborant_miqdor_ozgartira_olmaydi(self):
        self.as_laborant()
        r = self.client.patch(
            reverse('chemical-quantity', args=[self.chemical.pk]),
            {'action': 'add', 'amount': '100'}
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# -----------------------------------------------
# 5. ARXIVLASH
# -----------------------------------------------
class ChemicalDeactivateTest(ChemicalBaseTest):

    def test_admin_arxivlay_oladi(self):
        self.as_admin()
        r = self.client.patch(reverse('chemical-deactivate', args=[self.chemical.pk]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.chemical.refresh_from_db()
        self.assertFalse(self.chemical.is_active)

    def test_laborant_arxivlay_olmaydi(self):
        self.as_laborant()
        r = self.client.patch(reverse('chemical-deactivate', args=[self.chemical.pk]))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


# -----------------------------------------------
# 6. ALERT — ChemicalAlertSerializer
# -----------------------------------------------
class ChemicalAlertTest(ChemicalBaseTest):

    def test_alert_maydonlar_minimal(self):
        make_chemical(cas_number='111-11-1', expiry_date=date.today() - timedelta(days=1))
        self.as_laborant()
        r = self.client.get(reverse('chemical-alerts'))
        item = r.data['expired'][0]
        self.assertNotIn('created_at', item)
        self.assertNotIn('updated_at', item)
        self.assertNotIn('storage_condition', item)

    def test_expiring_soon(self):
        make_chemical(cas_number='222-22-2', expiry_date=date.today() + timedelta(days=10))
        self.as_laborant()
        r = self.client.get(reverse('chemical-alerts'))
        self.assertEqual(len(r.data['expiring_soon']), 1)

    def test_expired(self):
        make_chemical(cas_number='333-33-3', expiry_date=date.today() - timedelta(days=1))
        self.as_laborant()
        r = self.client.get(reverse('chemical-alerts'))
        self.assertEqual(len(r.data['expired']), 1)

    def test_low_stock(self):
        make_chemical(cas_number='444-44-4', quantity=Decimal('10'), min_threshold=Decimal('50'))
        self.as_laborant()
        r = self.client.get(reverse('chemical-alerts'))
        self.assertEqual(len(r.data['low_stock']), 1)
