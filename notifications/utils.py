"""
Envoi de notifications push aux médecins abonnés, via le protocole
Web Push (norme utilisée par tous les navigateurs modernes).
"""
import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import PushSubscription

logger = logging.getLogger(__name__)


def envoyer_notification(medecin, titre, corps, url="/"):
    """
    Envoie une notification push à TOUS les appareils sur lesquels
    ce médecin s'est abonné. Retourne le nombre de notifications
    envoyées avec succès.
    """
    payload = json.dumps({"title": titre, "body": corps, "url": url})
    envoyees = 0

    for abonnement in medecin.push_subscriptions.all():
        try:
            webpush(
                subscription_info=abonnement.to_subscription_info(),
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            )
            envoyees += 1
        except WebPushException as exc:
            # Abonnement expiré ou invalide (ex: appli désinstallée) : on
            # le supprime pour ne pas réessayer indéfiniment.
            logger.warning("Échec envoi push à %s : %s", medecin, exc)
            if exc.response is not None and exc.response.status_code in (404, 410):
                abonnement.delete()

    return envoyees
