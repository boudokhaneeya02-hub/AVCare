from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Medecin


class InscriptionMedecinForm(UserCreationForm):
    class Meta:
        model = Medecin
        fields = [
            "username", "first_name", "last_name", "email",
            "telephone", "specialite", "etablissement",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "specialite": forms.Select(attrs={"class": "form-select"}),
            "etablissement": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(
        label="Email ou identifiant",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
