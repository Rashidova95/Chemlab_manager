# ChemLab UZ — LIMS

**Kimyo laboratoriyalari uchun boshqaruv tizimi (Laboratory Information Management System)**

Django 4.2 + DRF + PostgreSQL asosida qurilgan MVP backend.

---

## Texnik stek

| Qatlam | Texnologiya |
|--------|------------|
| Backend | Django 4.2 + DRF 3.17 |
| Ma'lumotlar bazasi | PostgreSQL 15+ |
| Auth | JWT (djangorestframework-simplejwt) |
| PDF | ReportLab |
| API docs | drf-spectacular (Swagger) |

---

## O'rnatish

### 1. Reponi klonlash

```bash
  git clone https://github.com/Rashidova95/Chemlab_manager.git
  cd chemlab-uz
```

### 2. Virtual muhit

```bash
  python -m venv venv

# Windows
  venv\Scripts\activate

# Linux/Mac
  source venv/bin/activate
```

### 3. Kutubxonalarni o'rnatish

```bash
  pip install -r requirements.txt
```

### 4. `.env` fayl yaratish

```bash
  cp .env.example .env
# .env faylini o'zingizga mos o'zgartiring
```

### 5. PostgreSQL sozlash

```sql
CREATE DATABASE chem_db;
CREATE USER chem_user WITH PASSWORD 'strongpassword123';
GRANT ALL PRIVILEGES ON DATABASE chemlab_db TO chemlab_user;
```

### 6. Migration

```bash
  python manage.py migrate
```

### 7. Superuser yaratish

```bash
  python manage.py createsuperuser
```

### 8. Ishga tushirish

```bash
  python manage.py runserver
```

---

## API hujjatlar

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin panel**: http://localhost:8000/admin/

---

## Loyiha tuzilmasi

```
Chemlab_manager/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   └── dev.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/          # Auth, JWT, RBAC
│   ├── inventory/      # Kimyoviy moddalar
│   ├── samples/        # Namuna boshqaruvi
│   ├── experiments/    # Tajribalar (ELN)
│   ├── reports/        # PDF hisobot
│   └── dashboard/      # Statistika
├── .env.example
├── requirements.txt
└── manage.py
```

---

## Rol tizimi (RBAC)

| Rol | Huquqlar |
|-----|----------|
| `admin` | Barcha amallar |
| `chemist` | Ko'rish, yaratish, tasdiqlash |
| `laborant` | Ko'rish, yaratish |
| `viewer` | Faqat ko'rish va PDF yuklab olish |

---

## API endpointlar

### Auth
| Method | Endpoint | Huquq |
|--------|----------|-------|
| POST | `/api/v1/auth/register/` | Ochiq |
| POST | `/api/v1/auth/login/` | Ochiq |
| POST | `/api/v1/auth/refresh/` | Ochiq |
| GET/PATCH | `/api/v1/auth/me/` | JWT |
| POST | `/api/v1/auth/change-password/` | JWT |

### Inventory
| Method | Endpoint | Huquq |
|--------|----------|-------|
| GET | `/api/v1/chemicals/` | JWT |
| POST | `/api/v1/chemicals/create/` | Admin |
| GET | `/api/v1/chemicals/{id}/` | JWT |
| PATCH | `/api/v1/chemicals/{id}/update/` | Admin |
| PATCH | `/api/v1/chemicals/{id}/quantity/` | Chemist+ |
| PATCH | `/api/v1/chemicals/{id}/deactivate/` | Admin |
| GET | `/api/v1/chemicals/alerts/` | JWT |

### Samples
| Method | Endpoint | Huquq |
|--------|----------|-------|
| GET | `/api/v1/samples/` | JWT |
| POST | `/api/v1/samples/create/` | Laborant+ |
| GET | `/api/v1/samples/{id}/` | JWT |
| PATCH | `/api/v1/samples/{id}/status/` | Laborant+ |
| GET | `/api/v1/samples/export/csv/` | JWT |

### Experiments
| Method | Endpoint | Huquq |
|--------|----------|-------|
| GET | `/api/v1/experiments/` | JWT |
| POST | `/api/v1/experiments/create/` | Laborant+ |
| GET | `/api/v1/experiments/{id}/` | JWT |
| PATCH | `/api/v1/experiments/{id}/update/` | O'z tajribasi |
| PATCH | `/api/v1/experiments/{id}/approve/` | Chemist+ |
| PATCH | `/api/v1/experiments/{id}/reject/` | Chemist+ |

### Reports & Dashboard
| Method | Endpoint | Huquq |
|--------|----------|-------|
| GET | `/api/v1/reports/samples/{id}/pdf/` | JWT |
| GET | `/api/v1/dashboard/stats/` | JWT |

---

## Testlar

```bash
# Barcha testlar
  python manage.py test

# Modul bo'yicha
  python manage.py test apps.users
  python manage.py test apps.inventory
  python manage.py test apps.samples
  python manage.py test apps.experiments
```

---

## Docker bilan ishga tushirish

```bash
  docker-compose up --build
```

---

*ChemLab UZ — MVP v1.0 | 2026*
