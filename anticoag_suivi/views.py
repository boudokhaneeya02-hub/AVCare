from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def service_worker(request):
    """
    Sert le service worker à la racine du site (/sw.js) plutôt que sous
    /static/, afin qu'il contrôle TOUTE l'application (portée = '/')
    et pas seulement le dossier /static/.
    """
    chemin = Path(settings.BASE_DIR) / "static" / "sw.js"
    contenu = chemin.read_text(encoding="utf-8")
    return HttpResponse(contenu, content_type="application/javascript")
