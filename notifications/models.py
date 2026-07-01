from django.conf import settings
from django.db import models


class PushSubscription(models.Model):
    """
    Un abonnement push correspond à UN navigateur/appareil sur lequel
    un médecin a autorisé les notifications (ex: son téléphone, son PC
    du cabinet). Un même médecin peut avoir plusieurs abonnements.
    """

    medecin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.CharField(max_length=255, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Abonnement notification"
        verbose_name_plural = "Abonnements notifications"

    def __str__(self):
        return f"Abonnement de {self.medecin} ({self.user_agent[:40]})"

    def to_subscription_info(self):
        """Format attendu par pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            },
        }
