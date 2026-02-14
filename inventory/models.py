from django.db import models
from django.utils.translation import gettext_lazy as _


class Part(models.Model):
    code = models.CharField(_("Code"), max_length=100, unique=True)
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    current_stock = models.PositiveIntegerField(_("Current stock"), default=0)
    reserved = models.PositiveIntegerField(_("Reserved"), default=0)
    min_stock = models.PositiveIntegerField(_("Minimum stock"), default=0)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(_("Supplier"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Part")
        verbose_name_plural = _("Parts")

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    @property
    def available_stock(self) -> int:
        return self.current_stock - self.reserved

    def clean(self) -> None:
        super().clean()
        if self.reserved > self.current_stock:
            from django.core.exceptions import ValidationError

            raise ValidationError({"reserved": _("Reserved cannot exceed current stock.")})
