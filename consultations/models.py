from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse

from .inr_logic import interpreter_inr, comprimes_vers_mg_sintrom, suggerer_ajustement_dose


class RendezVous(models.Model):
    """Rendez-vous de contrôle (programmé tous les 15 jours / mois, etc.)."""

    STATUT_CHOICES = [
        ("planifie", "Planifié"),
        ("honore", "Honoré"),
        ("annule", "Annulé"),
        ("absent", "Patient absent"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="rendez_vous"
    )
    medecin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rendez_vous"
    )
    date_heure = models.DateTimeField()
    motif = models.CharField(
        max_length=255, blank=True, default="Contrôle INR de routine"
    )
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="planifie")
    annule = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_heure"]

    def __str__(self):
        return f"RDV {self.patient} — {self.date_heure:%d/%m/%Y %H:%M}"

    def get_absolute_url(self):
        return reverse("consultations:rdv_detail", args=[self.pk])


class Consultation(models.Model):
    """
    Consultation de suivi : INR mesuré, dose prescrite/prise, commentaires
    médicaux. Constitue l'historique INR / doses du patient.
    """

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="consultations"
    )
    medecin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consultations"
    )
    rendez_vous = models.ForeignKey(
        RendezVous, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="consultation",
    )

    date_consultation = models.DateTimeField()

    # --- INR ---
    valeur_inr = models.DecimalField(
        max_digits=4, decimal_places=2,
        help_text="Valeur mesurée de l'INR (ex : 2.40)",
    )

    # --- Dose ---
    dose_comprimes = models.DecimalField(
        max_digits=4, decimal_places=2,
        help_text="Nombre de comprimés de Sintrom 4 mg pris/prescrits par jour (ex : 0.5 = 1/2 cp)",
    )
    dose_libre = models.CharField(
        max_length=255, blank=True,
        help_text="Texte libre si le schéma de dose est variable (ex : alternance 1/2-1 cp)",
    )
    motif_ajustement_dose = models.TextField(
        blank=True,
        verbose_name="Motif de l'ajustement de dose",
        help_text=(
            "Obligatoire si la dose change par rapport à la consultation "
            "précédente : justification médicale du changement décidé."
        ),
    )

    # --- Événements hémorragiques ---
    EVENEMENTS_HEMORRAGIQUES_CHOICES = [
        ("avc_hemorragique", "AVC hémorragique"),
        ("hemorragie_digestive", "Hémorragie digestive"),
        ("hematurie", "Hématurie"),
        ("epistaxis", "Épistaxis (saignement de nez)"),
        ("gingivorragie", "Gingivorragie"),
        ("hematome", "Hématome / ecchymose importante"),
        ("hemoptysie", "Hémoptysie"),
        ("menorragie", "Ménorragie / saignement gynécologique"),
        ("autre_hemorragie", "Autre saignement"),
    ]

    # --- Événements thrombotiques / emboliques ---
    EVENEMENTS_THROMBOTIQUES_CHOICES = [
        ("avc_ischemique", "AVC ischémique"),
        ("ait", "Accident ischémique transitoire (AIT)"),
        ("embolie_pulmonaire", "Embolie pulmonaire"),
        ("thrombose_veineuse", "Thrombose veineuse profonde"),
        ("thrombose_prothese", "Thrombose de prothèse valvulaire"),
        ("ischemie_arterielle", "Ischémie artérielle périphérique"),
        ("autre_thrombose", "Autre événement thrombotique/embolique"),
    ]

    evenement_hemorragique = models.BooleanField(
        default=False, verbose_name="Événement hémorragique survenu depuis la dernière consultation"
    )
    types_evenements_hemorragiques = models.JSONField(
        default=list, blank=True,
        verbose_name="Type(s) d'événement hémorragique",
        help_text="Sélection parmi la liste, si un événement hémorragique est signalé.",
    )
    evenement_thrombotique = models.BooleanField(
        default=False, verbose_name="Événement thrombotique/embolique survenu depuis la dernière consultation"
    )
    types_evenements_thrombotiques = models.JSONField(
        default=list, blank=True,
        verbose_name="Type(s) d'événement thrombotique/embolique",
        help_text="Sélection parmi la liste, si un événement thrombotique/embolique est signalé.",
    )

    observance_signalee = models.CharField(
        max_length=20,
        choices=[
            ("bonne", "Bonne observance"),
            ("partielle", "Observance partielle"),
            ("mauvaise", "Mauvaise observance / oublis"),
        ],
        default="bonne",
    )

    commentaire_medical = models.TextField(
        blank=True, help_text="Observations cliniques, ajustements envisagés, etc."
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_consultation"]

    def __str__(self):
        return f"{self.patient} — INR {self.valeur_inr} le {self.date_consultation:%d/%m/%Y}"

    def get_absolute_url(self):
        return reverse("consultations:detail", args=[self.pk])

    @property
    def dose_mg(self):
        """Dose en mg pour le Sintrom 4 mg (1 comprimé = 4 mg)."""
        return comprimes_vers_mg_sintrom(self.dose_comprimes)

    @property
    def consultation_precedente(self):
        """Consultation immédiatement antérieure pour le même patient, s'il y en a une."""
        qs = self.patient.consultations.filter(date_consultation__lt=self.date_consultation)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs.order_by("-date_consultation").first()

    @property
    def changement_dose(self):
        """True si la dose de cette consultation diffère de la précédente."""
        precedente = self.consultation_precedente
        if precedente is None:
            return False
        return self.dose_comprimes != precedente.dose_comprimes

    @property
    def suggestion_ajustement(self):
        """
        Renvoie l'objet SuggestionAjustement (palier indicatif de variation de
        dose) basé sur l'INR de cette consultation et la dose actuellement
        en cours (celle de cette consultation, prise comme référence avant
        un éventuel changement). Aide indicative uniquement — voir inr_logic.py.
        """
        return suggerer_ajustement_dose(
            valeur_inr=self.valeur_inr,
            inr_cible_min=self.patient.inr_cible_min,
            inr_cible_max=self.patient.inr_cible_max,
            dose_actuelle_cp=self.dose_comprimes,
            saignement_signale=self.evenement_hemorragique,
        )

    def libelles_evenements_hemorragiques(self):
        mapping = dict(self.EVENEMENTS_HEMORRAGIQUES_CHOICES)
        return [mapping.get(code, code) for code in (self.types_evenements_hemorragiques or [])]

    def libelles_evenements_thrombotiques(self):
        mapping = dict(self.EVENEMENTS_THROMBOTIQUES_CHOICES)
        return [mapping.get(code, code) for code in (self.types_evenements_thrombotiques or [])]

    @property
    def interpretation(self):
        """
        Renvoie l'objet InterpretationINR pour cette consultation, basé sur
        la cible INR définie pour le patient. Aide à la lecture uniquement.
        """
        return interpreter_inr(
            valeur_inr=self.valeur_inr,
            inr_cible_min=self.patient.inr_cible_min,
            inr_cible_max=self.patient.inr_cible_max,
            saignement_signale=self.evenement_hemorragique,
            porteur_prothese_mecanique=self.patient.valve_mecanique,
        )
