from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Sample, SampleStatusLog

User = get_user_model()


# -----------------------------------------------
# URL NOMLARI —
# -----------------------------------------------
LIST_URL   = 'sample-list'
CREATE_URL = 'sample-create'
DETAIL_URL = 'sample-detail'
STATUS_URL = 'sample-status-update'
CSV_URL    = 'sample-csv-export'


# -----------------------------------------------
# YORDAMCHI
# -----------------------------------------------
def make_sample(**kwargs):
    defaults = {
        'name':        'Natriy xlorid',
        'source_type': 'industrial',
        'status':      'received',
        'quantity':    Decimal('250'),
        'unit':        'g',
    }
    defaults.update(kwargs)
    return Sample.objects.create(**defaults)


class SampleBaseTest(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@lab.uz', username='admin', password='Test1234!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.laborant = User.objects.create_user(
            email='laborant@lab.uz', username='laborant', password='Test1234!'
        )
        self.laborant.profile.role = 'laborant'
        self.laborant.profile.save()

        self.viewer = User.objects.create_user(
            email='viewer@lab.uz', username='viewer', password='Test1234!'
        )
        self.viewer.profile.role = 'viewer'
        self.viewer.profile.save()

        self.sample = make_sample(received_by=self.laborant)

    def as_admin(self):
        self.client.force_authenticate(user=self.admin)

    def as_laborant(self):
        self.client.force_authenticate(user=self.laborant)

    def as_viewer(self):
        self.client.force_authenticate(user=self.viewer)


# -----------------------------------------------
# 1. MODEL TESTLAR
# -----------------------------------------------
class SampleModelTest(SampleBaseTest):

    def test_sample_id_avtomatik(self):
        self.assertTrue(self.sample.sample_id.startswith('CHEM-'))

    def test_sample_id_format(self):
        parts = self.sample.sample_id.split('-')
        self.assertEqual(parts[0], 'CHEM')
        self.assertEqual(len(parts[2]), 5)

    def test_status_default_received(self):
        self.assertEqual(self.sample.status, 'received')

    def test_can_move_to_oldinga(self):
        self.assertTrue(self.sample.can_move_to('in_progress'))

    def test_can_move_to_orqaga(self):
        self.assertFalse(self.sample.can_move_to('received'))

    def test_can_move_to_ikki_qadam(self):
        self.assertFalse(self.sample.can_move_to('completed'))

    def test_str(self):
        self.assertIn('CHEM-', str(self.sample))
        self.assertIn('Natriy xlorid', str(self.sample))


# -----------------------------------------------
# 2. RO'YXAT
# -----------------------------------------------
class SampleListTest(SampleBaseTest):

    def test_royxat_200(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_token_siz_401(self):
        r = self.client.get(reverse(LIST_URL))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_royxatda_notes_yoq(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL))
        item = r.data['results'][0]
        self.assertNotIn('notes', item)

    def test_status_filtri(self):
        make_sample(status='completed', received_by=self.laborant)
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL), {'status': 'received'})
        for item in r.data['results']:
            self.assertEqual(item['status'], 'received')

    def test_qidiruv_ishlaydi(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL), {'search': self.sample.sample_id})
        self.assertEqual(r.data['count'], 1)


# -----------------------------------------------
# 3. YARATISH
# -----------------------------------------------
class SampleCreateTest(SampleBaseTest):

    def get_data(self, **kwargs):
        data = {
            'name':        'Kalsiy karbonat',
            'source_type': 'educational',
            'quantity':    100,
            'unit':        'g',
            'notes':       'Test namunasi',
        }
        data.update(kwargs)
        return data

    def test_laborant_yarata_oladi(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_viewer_yarata_olmaydi(self):
        self.as_viewer()
        r = self.client.post(reverse(CREATE_URL), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_received_by_avtomatik(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        sample = Sample.objects.filter(name='Kalsiy karbonat').first()
        self.assertEqual(sample.received_by, self.laborant)

    def test_sample_id_avtomatik(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data())
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        sample = Sample.objects.filter(name='Kalsiy karbonat').first()
        self.assertTrue(sample.sample_id.startswith('CHEM-'))


# -----------------------------------------------
# 4. DETAIL
# -----------------------------------------------
class SampleDetailTest(SampleBaseTest):

    def test_detail_200(self):
        self.as_laborant()
        r = self.client.get(reverse(DETAIL_URL, args=[self.sample.pk]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_notes_bor(self):
        self.as_laborant()
        r = self.client.get(reverse(DETAIL_URL, args=[self.sample.pk]))
        self.assertIn('notes', r.data)
        self.assertIn('sample_id', r.data)


# -----------------------------------------------
# 5. STATUS O'ZGARTIRISH
# -----------------------------------------------
class SampleStatusTest(SampleBaseTest):

    def test_oldinga_otadi(self):
        self.as_laborant()
        r = self.client.patch(
            reverse(STATUS_URL, args=[self.sample.pk]),
            {'status': 'in_progress'}
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.sample.refresh_from_db()
        self.assertEqual(self.sample.status, 'in_progress')

    def test_orqaga_otmaydi(self):
        self.sample.status = 'in_progress'
        self.sample.save()
        self.as_laborant()
        r = self.client.patch(
            reverse(STATUS_URL, args=[self.sample.pk]),
            {'status': 'received'}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ikki_qadam_otmaydi(self):
        self.as_laborant()
        r = self.client.patch(
            reverse(STATUS_URL, args=[self.sample.pk]),
            {'status': 'completed'}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_ozgartira_olmaydi(self):
        self.as_viewer()
        r = self.client.patch(
            reverse(STATUS_URL, args=[self.sample.pk]),
            {'status': 'in_progress'}
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_log_yoziladi(self):
        self.as_laborant()
        self.client.patch(
            reverse(STATUS_URL, args=[self.sample.pk]),
            {'status': 'in_progress'}
        )
        log = SampleStatusLog.objects.filter(sample=self.sample).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.old_status, 'received')
        self.assertEqual(log.new_status, 'in_progress')


# -----------------------------------------------
# 6. CSV EKSPORT
# -----------------------------------------------
class SampleCSVTest(SampleBaseTest):

    def test_csv_200(self):
        self.as_laborant()
        r = self.client.get(reverse(CSV_URL))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn(r['Content-Type'], 'text/csv')

    def test_token_siz_401(self):
        r = self.client.get(reverse(CSV_URL))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
