from django.contrib import admin
from .models import RendezVous, Consultation


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ("patient", "medecin", "date_heure", "statut")
    list_filter = ("statut", "medecin")
    date_hierarchy = "date_heure"


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "medecin", "date_consultation", "valeur_inr", "dose_comprimes", "evenement_hemorragique", "evenement_thrombotique")
    list_filter = ("medecin", "evenement_hemorragique", "evenement_thrombotique")
    date_hierarchy = "date_consultation"
