from django.urls import path
from . import views

app_name = "consultations"

urlpatterns = [
    path("agenda/", views.agenda, name="agenda"),
    path("patient/<int:patient_pk>/nouvelle/", views.creer_consultation, name="creer"),
    path("<int:pk>/", views.detail_consultation, name="detail"),
    path("patient/<int:patient_pk>/rdv/nouveau/", views.creer_rendez_vous, name="rdv_creer"),
    path("rdv/<int:pk>/", views.detail_rendez_vous, name="rdv_detail"),
    path("rdv/<int:pk>/modifier/", views.modifier_rendez_vous, name="rdv_modifier"),
]
