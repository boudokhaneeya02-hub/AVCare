from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("cle-publique/", views.cle_publique, name="cle_publique"),
    path("abonner/", views.enregistrer_abonnement, name="abonner"),
    path("desabonner/", views.supprimer_abonnement, name="desabonner"),
    path("tester/", views.tester_notification, name="tester"),
]
