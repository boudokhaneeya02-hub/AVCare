from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "nom", "prenom", "date_naissance", "sexe", "telephone", "adresse",
            "antecedents_medicaux", "indication", "date_evenement",
            "molecule_avk", "traitement_associe",
            "valve_mecanique", "type_valve",
            "inr_cible_min", "inr_cible_max",
            "uree", "creatinine", "ionogramme", "tp", "inr_biologie",
            "hemoglobine", "plaquettes", "date_bilan_biologique",
            "frequence_suivi", "actif",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "date_naissance": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "antecedents_medicaux": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "indication": forms.Select(attrs={"class": "form-select"}),
            "date_evenement": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "molecule_avk": forms.Select(attrs={"class": "form-select"}),
            "traitement_associe": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "valve_mecanique": forms.CheckboxInput(),
            "type_valve": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex : Saint Jude n°23, position mitrale"}),
            "inr_cible_min": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "inr_cible_max": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "uree": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "g/L"}),
            "creatinine": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "mg/L"}),
            "ionogramme": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex : Na+ 138, K+ 4.2 mmol/L"}),
            "tp": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "placeholder": "%"}),
            "inr_biologie": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "hemoglobine": forms.NumberInput(attrs={"class": "form-control", "step": "0.1", "placeholder": "g/dL"}),
            "plaquettes": forms.NumberInput(attrs={"class": "form-control", "placeholder": "/mm³"}),
            "date_bilan_biologique": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "frequence_suivi": forms.Select(attrs={"class": "form-select"}),
            "actif": forms.CheckboxInput(),
        }

    def clean(self):
        cleaned = super().clean()
        cible_min = cleaned.get("inr_cible_min")
        cible_max = cleaned.get("inr_cible_max")
        if cible_min is not None and cible_max is not None and cible_min >= cible_max:
            raise forms.ValidationError(
                "La borne basse de la cible INR doit être inférieure à la borne haute."
            )
        return cleaned
