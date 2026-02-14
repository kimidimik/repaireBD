from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from repairs.models import Device


DEFAULT_DEVICES = ["Advance Mei Bill", "Bill UBAPRO", "CashCode Bill", "Counter Board"]


class Command(BaseCommand):
    help = "Create base groups and predefined devices"

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        tech_group, _ = Group.objects.get_or_create(name="Technician")

        tech_perms = Permission.objects.filter(
            content_type__app_label="repairs",
            codename__in=["add_repair", "change_repair", "view_repair", "add_repairpartusage", "change_repairpartusage"],
        )
        tech_group.permissions.set(tech_perms)

        admin_perms = Permission.objects.all()
        admin_group.permissions.set(admin_perms)

        for name in DEFAULT_DEVICES:
            Device.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Workshop bootstrap completed."))
