from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import Part
from repairs.models import Device, Repair, RepairPartUsage


class RepairStockLogicTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tech", password="x")
        self.device = Device.objects.create(name="CashCode Bill")
        self.part = Part.objects.create(code="BELT-320", name="Belt", current_stock=5)
        self.repair = Repair.objects.create(
            device=self.device,
            created_by=self.user,
            serial_number="SN123",
            defect="Does not accept bills",
        )

    def test_usage_reserves_stock(self):
        RepairPartUsage.objects.create(repair=self.repair, part=self.part, quantity=2)
        self.part.refresh_from_db()
        self.assertEqual(self.part.reserved, 2)

    def test_cannot_reserve_more_than_available(self):
        with self.assertRaises(ValidationError):
            RepairPartUsage.objects.create(repair=self.repair, part=self.part, quantity=8)

    def test_completed_writes_off_parts(self):
        RepairPartUsage.objects.create(repair=self.repair, part=self.part, quantity=3)
        self.repair.status = Repair.Status.COMPLETED
        self.repair.save()
        self.part.refresh_from_db()
        self.assertEqual(self.part.current_stock, 2)
        self.assertEqual(self.part.reserved, 0)
