import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import PushSubscription
from .utils import envoyer_notification


@login_required
@require_POST
def enregistrer_abonnement(request):
    """
    Appelée en JS juste après que le médecin ait accepté les notifications
    dans son navigateur. Enregistre (ou met à jour) son abonnement push.
    """
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "erreur": "Données invalides"}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "medecin": request.user,
            "p256dh": keys.get("p256dh", ""),
            "auth": keys.get("auth", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
        },
    )
    return JsonResponse({"ok": True})


@login_required
@require_POST
def supprimer_abonnement(request):
    """Appelée si le médecin désactive les notifications dans son navigateur."""
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({"ok": False}, status=400)

    PushSubscription.objects.filter(endpoint=endpoint, medecin=request.user).delete()
    return JsonResponse({"ok": True})


@login_required
def cle_publique(request):
    """Fournit la clé publique VAPID au JS du navigateur pour l'abonnement."""
    return JsonResponse({"vapidPublicKey": settings.VAPID_PUBLIC_KEY})


@login_required
@require_POST
def tester_notification(request):
    """Bouton 'Tester les notifications' : le médecin s'envoie un message à lui-même."""
    envoyees = envoyer_notification(
        request.user,
        titre="AVCare",
        corps="Les notifications fonctionnent sur cet appareil ✅",
        url="/",
    )
    if envoyees == 0:
        return JsonResponse(
            {"ok": False, "erreur": "Aucun appareil abonné. Active d'abord les notifications."}
        )
    return JsonResponse({"ok": True, "envoyees": envoyees})
