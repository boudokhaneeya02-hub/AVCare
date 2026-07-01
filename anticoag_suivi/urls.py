from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sw.js", views.service_worker, name="service_worker"),
    path("comptes/", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("suivi/", include("consultations.urls")),
    path("notifications/", include("notifications.urls")),
    path("", RedirectView.as_view(pattern_name="patients:liste", permanent=False)),
    path(
    "service-worker.js",
    TemplateView.as_view(
        template_name="service-worker.js",
        content_type="application/javascript"
    ),
    name="service_worker"
),
]
