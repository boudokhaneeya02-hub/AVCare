from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Medecin


@admin.register(Medecin)
class MedecinAdmin(UserAdmin):
    model = Medecin
    list_display = ("username", "email", "first_name", "last_name", "specialite", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Informations professionnelles", {
            "fields": ("telephone", "specialite", "etablissement"),
        }),
    )
