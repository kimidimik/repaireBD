# Electronics Repair Workshop (Django Admin)

Production-oriented Django 5 application for repair workshop management focused on bill acceptors/coin validators. UI is implemented exclusively through Django Admin.

## Features
- Repairs tracking by device and serial number
- Stock and part reservation using through model (`RepairPartUsage`)
- Automatic write-off when repair is completed/closed
- Telegram notifications on status changes
- Role model with `Admin` and `Technician` groups
- Multilingual admin (EN / UK / RO)
- Admin statistics (completed per period, top devices/defects, difficulty breakdown)

## Tech stack
- Python 3.11+
- Django 5.x
- PostgreSQL

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure PostgreSQL and environment variables.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py bootstrap_workshop
python manage.py runserver
```

## i18n
Translatable strings are marked with `gettext_lazy`.

```bash
python manage.py makemessages -l uk -l ro -l en
python manage.py compilemessages
```

Language switch is enabled with `LocaleMiddleware` and `/i18n/setlang/` endpoint.

## Business logic summary
- Adding/updating `RepairPartUsage` reserves part quantities (`Part.reserved`).
- Reservation is blocked if available stock (`current_stock - reserved`) would go negative.
- Setting `Repair.status` to `Completed`/`Closed` writes off used parts and clears reservation for those rows.
- Admin actions:
  - Mark as Completed
  - Write-off parts
  - Release reserved parts

## Tests
`repairs/tests.py` covers reservation and write-off logic.
