from django.conf import settings
from django.db import models
from django.urls import reverse


class Patient(models.Model):
    """
    Fiche patient complète pour le suivi sous AVK.
    Chaque patient est rattaché à un médecin (isolation multi-comptes).
    """

    SEXE_CHOICES = [
        ("M", "Masculin"),
        ("F", "Féminin"),
    ]

    INDICATION_CHOICES = [
        ("avc_ischemique", "AVC ischémique"),
        ("avc_hemorragique", "AVC hémorragique (séquellaire)"),
        ("ait", "Accident ischémique transitoire (AIT)"),
        ("fibrillation_atriale", "Fibrillation atriale"),
        ("embolie_pulmonaire", "Embolie pulmonaire"),
        ("thrombose_veineuse", "Thrombose veineuse (profonde)"),
        ("prothese_mecanique_aortique", "Prothèse mécanique aortique"),
        ("prothese_mecanique_mitrale", "Prothèse mécanique mitrale"),
        ("autre", "Autre indication"),
    ]

    # Indications pour lesquelles le patient porte une prothèse mécanique
    # (utilisé pour la cible INR par défaut et les alertes de sous-dosage).
    INDICATIONS_PROTHESE_MECANIQUE = {
        "prothese_mecanique_aortique",
        "prothese_mecanique_mitrale",
    }

    AVK_MOLECULE_CHOICES = [
        ("acenocoumarol", "Acénocoumarol (Sintrom 4 mg)"),
        ("warfarine", "Warfarine"),
        ("fluindione", "Fluindione (Préviscan)"),
        ("autre", "Autre AVK"),
    ]

    # --- Rattachement médecin ---
    medecin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patients",
    )

    # --- Identité ---
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    # --- Antécédents et contexte médical ---
    antecedents_medicaux = models.TextField(
        blank=True,
        help_text="HTA, diabète, cardiopathie, antécédents hémorragiques, etc.",
    )
    indication = models.CharField(
        max_length=30, choices=INDICATION_CHOICES, default="fibrillation_atriale",
        verbose_name="Indication du traitement AVK",
    )
    date_evenement = models.DateField(
        null=True, blank=True,
        verbose_name="Date de l'événement",
        help_text="Date de l'événement médical initial (AVC, embolie, thrombose, pose de prothèse, etc.)",
    )

    # --- Traitement actuel ---
    molecule_avk = models.CharField(
        max_length=20, choices=AVK_MOLECULE_CHOICES, default="acenocoumarol"
    )
    traitement_associe = models.TextField(
        blank=True,
        help_text="Autres traitements en cours (antihypertenseurs, statines, etc.)",
    )

    # --- Configuration de la cible INR (validée et modifiable par le médecin) ---
    valve_mecanique = models.BooleanField(
        default=False,
        verbose_name="Porteur d'une prothèse cardiaque mécanique",
        help_text="Renseigné automatiquement selon l'indication ; modifie la cible INR et la sensibilité des alertes de sous-dosage.",
    )
    type_valve = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Précision sur la prothèse",
        help_text="Type/modèle de la prothèse, si applicable.",
    )
    inr_cible_min = models.DecimalField(
        max_digits=3, decimal_places=1, default=2.0,
        help_text="Borne basse de la cible INR pour ce patient (modifiable par le médecin).",
    )
    inr_cible_max = models.DecimalField(
        max_digits=3, decimal_places=1, default=3.0,
        help_text="Borne haute de la cible INR pour ce patient (modifiable par le médecin).",
    )

    # --- Paramètres biologiques (derniers résultats connus) ---
    uree = models.DecimalField(
        "Urée (g/L)", max_digits=5, decimal_places=2, null=True, blank=True,
    )
    creatinine = models.DecimalField(
        "Créatinine (mg/L)", max_digits=5, decimal_places=2, null=True, blank=True,
    )
    ionogramme = models.CharField(
        "Ionogramme sanguin", max_length=255, blank=True,
        help_text="ex : Na+ 138 mmol/L, K+ 4.2 mmol/L",
    )
    tp = models.DecimalField(
        "TP — taux de prothrombine (%)", max_digits=5, decimal_places=1, null=True, blank=True,
    )
    inr_biologie = models.DecimalField(
        "INR (dernier bilan biologique)", max_digits=4, decimal_places=2, null=True, blank=True,
        help_text="Valeur de référence issue du bilan biologique global, distincte du suivi de consultation.",
    )
    hemoglobine = models.DecimalField(
        "Hémoglobine (g/dL)", max_digits=4, decimal_places=1, null=True, blank=True,
    )
    plaquettes = models.PositiveIntegerField(
        "Plaquettes (/mm³)", null=True, blank=True,
    )
    date_bilan_biologique = models.DateField(
        "Date du bilan biologique", null=True, blank=True,
    )

    # --- Suivi ---
    FREQUENCE_CHOICES = [
        ("15j", "Tous les 15 jours"),
        ("1m", "Tous les mois"),
        ("autre", "Autre / à définir"),
    ]
    frequence_suivi = models.CharField(
        max_length=10, choices=FREQUENCE_CHOICES, default="1m"
    )

    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom.upper()} {self.prenom}"

    def get_absolute_url(self):
        return reverse("patients:detail", args=[self.pk])

    def appliquer_cible_par_defaut(self):
        """
        Applique la cible INR par défaut selon l'indication (prothèse
        mécanique ou non). N'écrase pas une valeur déjà personnalisée
        volontairement par le médecin — à utiliser uniquement à la création
        ou sur demande explicite.
        """
        if self.indication in self.INDICATIONS_PROTHESE_MECANIQUE:
            self.valve_mecanique = True
            self.inr_cible_min = 2.5
            self.inr_cible_max = 3.5
        else:
            self.inr_cible_min = 2.0
            self.inr_cible_max = 3.0

    @property
    def age(self):
        if not self.date_naissance:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    @property
    def derniere_consultation(self):
        return self.consultations.order_by("-date_consultation").first()

    @property
    def prochain_rdv(self):
        from django.utils import timezone
        return (
            self.rendez_vous.filter(date_heure__gte=timezone.now(), annule=False)
            .order_by("date_heure")
            .first()
        )
