from django.contrib.auth.models import AbstractUser
from django.db import models


class Medecin(AbstractUser):
    """
    Compte utilisateur représentant un médecin.
    Hérite du système d'authentification Django (email + mot de passe,
    hashage sécurisé, gestion de session).
    Chaque médecin ne voit que ses propres patients (isolation des données).
    """
    SPECIALITE_CHOICES = [
        ("neurologie", "Neurologie"),
        ("cardiologie", "Cardiologie"),
        ("medecine_generale", "Médecine générale"),
        ("autre", "Autre"),
    ]

    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=30, blank=True)
    specialite = models.CharField(
        max_length=30, choices=SPECIALITE_CHOICES, default="medecine_generale"
    )
    etablissement = models.CharField(
        max_length=255, blank=True, help_text="Hôpital / clinique / cabinet"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"Dr {self.get_full_name() or self.username}"
