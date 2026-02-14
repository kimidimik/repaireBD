import logging

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.telegram import send_telegram_message
from repairs.models import Repair

logger = logging.getLogger("repairs")


@receiver(pre_save, sender=Repair)
def write_off_parts_on_status_change(sender, instance: Repair, **kwargs):
    old_status = None
    if instance.pk:
        old_status = sender.objects.filter(pk=instance.pk).values_list("status", flat=True).first()

    if old_status == instance.status:
        return

    if instance.status in {Repair.Status.COMPLETED, Repair.Status.CLOSED} and instance.pk:
        try:
            instance.write_off_parts()
            logger.info("Write-off performed for repair %s", instance.pk)
        except ValidationError:
            raise


@receiver(post_save, sender=Repair)
def notify_status_change(sender, instance: Repair, created: bool, **kwargs):
    if created:
        return

    watched = {Repair.Status.AWAITING_PARTS, Repair.Status.COMPLETED, Repair.Status.CLOSED}
    if instance.status not in watched:
        return

    awaiting_parts = ", ".join(
        f"{usage.part.code} x{usage.quantity}" for usage in instance.part_usages.select_related("part")
    )
    message = (
        f"Repair #{instance.pk} | {instance.device.name} | SN: {instance.serial_number} | "
        f"Status changed to {instance.status}"
    )
    if awaiting_parts:
        message += f" | Awaiting: {awaiting_parts}"
    send_telegram_message(message)
