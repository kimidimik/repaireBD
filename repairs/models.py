from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("Device")
        verbose_name_plural = _("Devices")

    def __str__(self) -> str:
        return self.name


class Repair(models.Model):
    class Difficulty(models.TextChoices):
        TEST = "Test", _("Test")
        SIMPLE = "Simple", _("Simple")
        NORMAL = "Normal", _("Normal")
        DIFFICULT = "Difficult", _("Difficult")
        VERY_DIFFICULT = "Very Difficult", _("Very Difficult")

    class Status(models.TextChoices):
        NEW = "New", _("New")
        AWAITING_PARTS = "Awaiting Parts", _("Awaiting Parts")
        IN_PROGRESS = "In Progress", _("In Progress")
        COMPLETED = "Completed", _("Completed")
        CLOSED = "Closed", _("Closed")

    class RepairType(models.TextChoices):
        REPLACEMENT = "Replacement", _("Replacement")
        CLEANING = "Cleaning", _("Cleaning")
        DIAGNOSTICS = "Diagnostics", _("Diagnostics")
        FIRMWARE = "Firmware", _("Firmware")

    created_at = models.DateField(_("Created at"), auto_now_add=True)
    device = models.ForeignKey(Device, verbose_name=_("Device"), on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Technician"),
        on_delete=models.PROTECT,
        related_name="repairs",
    )
    serial_number = models.CharField(_("Serial number"), max_length=50, db_index=True)
    defect = models.TextField(_("Defect"))
    repair_difficulty = models.CharField(
        _("Repair difficulty"),
        max_length=32,
        choices=Difficulty.choices,
        default=Difficulty.NORMAL,
    )
    status = models.CharField(_("Status"), max_length=32, choices=Status.choices, default=Status.NEW, db_index=True)
    type_of_repair = models.CharField(
        _("Type of repair"),
        max_length=32,
        choices=RepairType.choices,
        blank=True,
    )
    parts_used = models.ManyToManyField("inventory.Part", through="RepairPartUsage", related_name="repairs")
    note = models.TextField(_("Note"), blank=True)

    class Meta:
        verbose_name = _("Repair")
        verbose_name_plural = _("Repairs")
        indexes = [
            models.Index(fields=["serial_number"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} {self.device} ({self.serial_number})"

    def clean(self) -> None:
        super().clean()
        if self.pk and self.status in {self.Status.COMPLETED, self.Status.CLOSED}:
            for usage in self.part_usages.select_related("part"):
                if usage.part.current_stock < usage.quantity:
                    raise ValidationError(
                        _("Not enough stock to complete repair for part %(part)s.") % {"part": usage.part.code}
                    )

    @property
    def total_parts_cost(self) -> Decimal:
        total = Decimal("0.00")
        for usage in self.part_usages.select_related("part"):
            if usage.part.price:
                total += usage.part.price * usage.quantity
        return total

    @transaction.atomic
    def write_off_parts(self) -> None:
        usages = self.part_usages.select_for_update().select_related("part")
        for usage in usages:
            if usage.written_off:
                continue
            part = usage.part
            if part.current_stock < usage.quantity:
                raise ValidationError(_("Insufficient stock for %(part)s") % {"part": part.code})
            part.current_stock -= usage.quantity
            part.reserved = max(part.reserved - usage.quantity, 0)
            part.full_clean()
            part.save(update_fields=["current_stock", "reserved"])
            usage.written_off = True
            usage.save(update_fields=["written_off"])

    @transaction.atomic
    def release_reserved_parts(self) -> None:
        usages = self.part_usages.select_for_update().select_related("part")
        for usage in usages:
            if usage.written_off:
                continue
            part = usage.part
            part.reserved = max(part.reserved - usage.quantity, 0)
            part.full_clean()
            part.save(update_fields=["reserved"])


class RepairPartUsage(models.Model):
    repair = models.ForeignKey(Repair, on_delete=models.CASCADE, related_name="part_usages", verbose_name=_("Repair"))
    part = models.ForeignKey("inventory.Part", on_delete=models.PROTECT, verbose_name=_("Part"))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    date_used = models.DateTimeField(_("Date used"), auto_now_add=True)
    written_off = models.BooleanField(_("Written off"), default=False)

    class Meta:
        verbose_name = _("Repair part usage")
        verbose_name_plural = _("Repair part usages")
        unique_together = ("repair", "part")

    def __str__(self) -> str:
        return f"{self.repair_id}: {self.part.code} x{self.quantity}"

    def clean(self) -> None:
        super().clean()
        if self.quantity < 1:
            raise ValidationError({"quantity": _("Quantity must be positive.")})


    def save(self, *args, **kwargs):
        with transaction.atomic():
            previous_quantity = 0
            if self.pk:
                previous_quantity = (
                    RepairPartUsage.objects.select_for_update()
                    .filter(pk=self.pk)
                    .values_list("quantity", flat=True)
                    .first()
                    or 0
                )
            super().save(*args, **kwargs)
            delta = self.quantity - previous_quantity
            if delta > 0:
                part = type(self.part).objects.select_for_update().get(pk=self.part_id)
                if part.available_stock < delta:
                    raise ValidationError(_("Not enough available stock for %(part)s") % {"part": part.code})
                part.reserved += delta
                part.full_clean()
                part.save(update_fields=["reserved"])
            elif delta < 0:
                part = type(self.part).objects.select_for_update().get(pk=self.part_id)
                part.reserved = max(part.reserved + delta, 0)
                part.full_clean()
                part.save(update_fields=["reserved"])

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if not self.written_off:
                part = type(self.part).objects.select_for_update().get(pk=self.part_id)
                part.reserved = max(part.reserved - self.quantity, 0)
                part.full_clean()
                part.save(update_fields=["reserved"])
            return super().delete(*args, **kwargs)

