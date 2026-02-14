from django.apps import AppConfig


class RepairsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "repairs"

    def ready(self) -> None:
        import repairs.signals  # noqa: F401
