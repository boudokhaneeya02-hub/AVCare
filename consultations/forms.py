from django import forms
from .models import Consultation, RendezVous


class ConsultationForm(forms.ModelForm):
    types_evenements_hemorragiques = forms.MultipleChoiceField(
        choices=Consultation.EVENEMENTS_HEMORRAGIQUES_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Type(s) d'événement hémorragique",
    )
    types_evenements_thrombotiques = forms.MultipleChoiceField(
        choices=Consultation.EVENEMENTS_THROMBOTIQUES_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Type(s) d'événement thrombotique/embolique",
    )

    class Meta:
        model = Consultation
        fields = [
            "date_consultation", "valeur_inr",
            "dose_comprimes", "dose_libre", "motif_ajustement_dose",
            "evenement_hemorragique", "types_evenements_hemorragiques",
            "evenement_thrombotique", "types_evenements_thrombotiques",
            "observance_signalee",
            "commentaire_medical",
        ]
        widgets = {
            "date_consultation": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "valeur_inr": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "ex : 2.40"}),
            "dose_comprimes": forms.NumberInput(attrs={"class": "form-control", "step": "0.25", "min": "0", "placeholder": "ex : 0.5"}),
            "dose_libre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex : alternance 1/2 - 1 comprimé"}),
            "motif_ajustement_dose": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "ex : INR sous la cible à deux contrôles consécutifs, hausse décidée."}),
            "evenement_hemorragique": forms.CheckboxInput(),
            "evenement_thrombotique": forms.CheckboxInput(),
            "observance_signalee": forms.Select(attrs={"class": "form-select"}),
            "commentaire_medical": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, dose_precedente=None, **kwargs):
        """
        :param dose_precedente: Decimal ou None — dose en comprimés/jour de
            la consultation précédente du patient, utilisée pour exiger un
            motif si la nouvelle dose saisie diffère.
        """
        super().__init__(*args, **kwargs)
        self.dose_precedente = dose_precedente
        if self.instance and self.instance.pk:
            self.fields["types_evenements_hemorragiques"].initial = self.instance.types_evenements_hemorragiques
            self.fields["types_evenements_thrombotiques"].initial = self.instance.types_evenements_thrombotiques

    def clean_valeur_inr(self):
        valeur = self.cleaned_data["valeur_inr"]
        if valeur <= 0 or valeur > 15:
            raise forms.ValidationError("Valeur d'INR improbable. Vérifiez la saisie.")
        return valeur

    def clean(self):
        cleaned = super().clean()
        nouvelle_dose = cleaned.get("dose_comprimes")
        motif = (cleaned.get("motif_ajustement_dose") or "").strip()

        if (
            self.dose_precedente is not None
            and nouvelle_dose is not None
            and nouvelle_dose != self.dose_precedente
            and not motif
        ):
            self.add_error(
                "motif_ajustement_dose",
                "La dose a changé par rapport à la consultation précédente "
                f"({self.dose_precedente} cp/jour → {nouvelle_dose} cp/jour) : "
                "merci de préciser le motif de cet ajustement.",
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.types_evenements_hemorragiques = self.cleaned_data.get("types_evenements_hemorragiques", [])
        instance.types_evenements_thrombotiques = self.cleaned_data.get("types_evenements_thrombotiques", [])
        if commit:
            instance.save()
        return instance


class RendezVousForm(forms.ModelForm):
    class Meta:
        model = RendezVous
        fields = ["date_heure", "motif", "statut", "notes"]
        widgets = {
            "date_heure": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "motif": forms.TextInput(attrs={"class": "form-control"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le statut n'est pas demandé à la création (le template ne l'affiche
        # que pour la modification) : on le rend facultatif et on lui donne
        # une valeur par défaut dans save().
        self.fields["statut"].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.statut:
            instance.statut = "planifie"
        if commit:
            instance.save()
        return instance