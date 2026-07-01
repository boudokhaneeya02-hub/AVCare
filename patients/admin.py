from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "medecin", "indication", "valve_mecanique", "inr_cible_min", "inr_cible_max", "actif")
    list_filter = ("medecin", "indication", "valve_mecanique", "actif")
    search_fields = ("nom", "prenom")
