from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventory.models import Chemical
from apps.samples.models import Sample
from .models import Experiment

User = get_user_model()

# -----------------------------------------------
# URL NOMLARI
# -----------------------------------------------
LIST_URL = 'experiment-list'
CREATE_URL = 'experiment-create'
DETAIL_URL = 'experiment-detail'
UPDATE_URL = 'experiment-update'
APPROVE_URL = 'experiment-approve'
REJECT_URL = 'experiment-reject'


# -----------------------------------------------
# YORDAMCHI
# -----------------------------------------------
def make_sample(user):
    return Sample.objects.create(
        name='Test namuna',
        source_type='industrial',
        quantity=Decimal('100'),
        unit='g',
        received_by=user,
    )


def make_chemical():
    return Chemical.objects.create(
        name_uz='Sulfat kislota',
        name_iupac='Sulfuric acid',
        cas_number='7664-93-9',
        quantity=Decimal('500'),
        unit='ml',
        min_threshold=Decimal('50'),
        expiry_date=date.today() + timedelta(days=60),
        hazard_level=3,
    )


def make_experiment(sample, user, **kwargs):
    defaults = {
        'title': 'Azot tahlili',
        'method': 'Kjeldahl',
        'objective': 'Azot miqdorini aniqlash',
        'status': 'draft',
        'performed_by': user,
    }
    defaults.update(kwargs)
    return Experiment.objects.create(sample=sample, **defaults)


class ExperimentBaseTest(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@lab.uz', username='admin', password='Test1234!'
        )
        self.admin.profile.role = 'admin'
        self.admin.profile.save()

        self.chemist = User.objects.create_user(
            email='chemist@lab.uz', username='chemist', password='Test1234!'
        )
        self.chemist.profile.role = 'chemist'
        self.chemist.profile.save()

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

        self.sample = make_sample(self.laborant)
        self.chemical = make_chemical()
        self.experiment = make_experiment(self.sample, self.laborant)

    def as_admin(self):
        self.client.force_authenticate(user=self.admin)

    def as_chemist(self):
        self.client.force_authenticate(user=self.chemist)

    def as_laborant(self):
        self.client.force_authenticate(user=self.laborant)

    def as_viewer(self):
        self.client.force_authenticate(user=self.viewer)


# -----------------------------------------------
# 1. RO'YXAT
# -----------------------------------------------
class ExperimentListTest(ExperimentBaseTest):

    def test_royxat_200(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_token_siz_401(self):
        r = self.client.get(reverse(LIST_URL))
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_royxatda_detail_maydonlar_yoq(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL))
        item = r.data['results'][0]
        self.assertNotIn('results', item)
        self.assertNotIn('observations', item)
        self.assertNotIn('rejection_reason', item)

    def test_status_filtri(self):
        make_experiment(self.sample, self.laborant, title='Test 2', status='review')
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL), {'status': 'draft'})
        for item in r.data['results']:
            self.assertEqual(item['status'], 'draft')

    def test_sample_filtri(self):
        self.as_laborant()
        r = self.client.get(reverse(LIST_URL), {'sample': self.sample.pk})
        self.assertEqual(r.data['count'], 1)


# -----------------------------------------------
# 2. YARATISH
# -----------------------------------------------
class ExperimentCreateTest(ExperimentBaseTest):

    def get_data(self, **kwargs):
        data = {
            'sample': self.sample.pk,
            'title': 'Fosfor tahlili',
            'method': 'Spektrofotometrik',
            'objective': 'Fosfor miqdorini aniqlash',
            'results': {},
        }
        data.update(kwargs)
        return data

    def test_laborant_yarata_oladi(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data(), format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_viewer_yarata_olmaydi(self):
        self.as_viewer()
        r = self.client.post(reverse(CREATE_URL), self.get_data(), format='json')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_performed_by_avtomatik(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data(), format='json')
        exp = Experiment.objects.filter(title='Fosfor tahlili').first()
        self.assertEqual(exp.performed_by, self.laborant)

    def test_status_default_draft(self):
        self.as_laborant()
        r = self.client.post(reverse(CREATE_URL), self.get_data(), format='json')
        exp = Experiment.objects.filter(title='Fosfor tahlili').first()
        self.assertEqual(exp.status, 'draft')


# -----------------------------------------------
# 3. DETAIL
# -----------------------------------------------
class ExperimentDetailTest(ExperimentBaseTest):

    def test_detail_200(self):
        self.as_laborant()
        r = self.client.get(reverse(DETAIL_URL, args=[self.experiment.pk]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_detail_barcha_maydonlar(self):
        self.as_laborant()
        r = self.client.get(reverse(DETAIL_URL, args=[self.experiment.pk]))
        self.assertIn('results', r.data)
        self.assertIn('observations', r.data)
        self.assertIn('chemicals_used', r.data)
        self.assertIn('rejection_reason', r.data)


# -----------------------------------------------
# 4. TAHRIRLASH
# -----------------------------------------------
class ExperimentUpdateTest(ExperimentBaseTest):

    def test_laborant_tahrirlaydi(self):
        self.as_laborant()
        r = self.client.patch(
            reverse(UPDATE_URL, args=[self.experiment.pk]),
            {'title': 'Yangilangan tahlil'},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_boshqa_laborant_tahrirlayolmaydi(self):
        other = User.objects.create_user(
            email='other@lab.uz', username='other', password='Test1234!'
        )
        other.profile.role = 'laborant'
        other.profile.save()
        self.client.force_authenticate(user=other)
        r = self.client.patch(
            reverse(UPDATE_URL, args=[self.experiment.pk]),
            {'title': 'Boshqa'},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_approved_tajribani_tahrirlayolmaydi(self):
        self.experiment.status = 'approved'
        self.experiment.save()
        self.as_laborant()
        r = self.client.patch(
            reverse(UPDATE_URL, args=[self.experiment.pk]),
            {'title': 'O\'zgartirishga urinish'},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------
# 5. TASDIQLASH
# -----------------------------------------------
class ExperimentApproveTest(ExperimentBaseTest):

    def setUp(self):
        super().setUp()
        self.experiment.status = 'review'
        self.experiment.save()

    def test_chemist_tasdiqlaydi(self):
        self.as_chemist()
        r = self.client.patch(reverse(APPROVE_URL, args=[self.experiment.pk]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, 'approved')
        self.assertEqual(self.experiment.approved_by, self.chemist)
        self.assertIsNotNone(self.experiment.approved_at)

    def test_laborant_tasdiqlay_olmaydi(self):
        self.as_laborant()
        r = self.client.patch(reverse(APPROVE_URL, args=[self.experiment.pk]))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_emasni_tasdiqlab_bolmaydi(self):
        self.experiment.status = 'draft'
        self.experiment.save()
        self.as_chemist()
        r = self.client.patch(reverse(APPROVE_URL, args=[self.experiment.pk]))
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------
# 6. QAYTARISH
# -----------------------------------------------
class ExperimentRejectTest(ExperimentBaseTest):

    def setUp(self):
        super().setUp()
        self.experiment.status = 'review'
        self.experiment.save()

    def test_chemist_qaytaradi(self):
        self.as_chemist()
        r = self.client.patch(
            reverse(REJECT_URL, args=[self.experiment.pk]),
            {'rejection_reason': 'Natijalar noto\'g\'ri'},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.experiment.refresh_from_db()
        self.assertEqual(self.experiment.status, 'rejected')
        self.assertEqual(self.experiment.rejection_reason, "Natijalar noto'g'ri")

    def test_sabab_siz_qaytarib_bolmaydi(self):
        self.as_chemist()
        r = self.client.patch(
            reverse(REJECT_URL, args=[self.experiment.pk]),
            {'rejection_reason': ''},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_laborant_qaytaraolmaydi(self):
        self.as_laborant()
        r = self.client.patch(
            reverse(REJECT_URL, args=[self.experiment.pk]),
            {'rejection_reason': 'Sabab'},
            format='json'
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
