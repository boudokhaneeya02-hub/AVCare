from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import InscriptionMedecinForm, ConnexionForm


class InscriptionView(CreateView):
    form_class = InscriptionMedecinForm
    template_name = "accounts/inscription.html"
    success_url = reverse_lazy("patients:liste")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ConnexionView(LoginView):
    authentication_form = ConnexionForm
    template_name = "accounts/connexion.html"


class DeconnexionView(LogoutView):
    pass
