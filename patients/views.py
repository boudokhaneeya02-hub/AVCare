from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import PatientForm
from .models import Patient


class MedecinOwnedQuerysetMixin:
    """Garantit qu'un médecin ne peut accéder qu'à SES patients."""

    def get_queryset(self):
        return Patient.objects.filter(medecin=self.request.user)


@login_required
def liste_patients(request):
    q = request.GET.get("q", "").strip()
    filtre = request.GET.get("filtre", "actifs")

    patients = Patient.objects.filter(medecin=request.user)

    if filtre == "actifs":
        patients = patients.filter(actif=True)
    elif filtre == "inactifs":
        patients = patients.filter(actif=False)

    if q:
        patients = patients.filter(Q(nom__icontains=q) | Q(prenom__icontains=q))

    # Statistiques rapides pour le tableau de bord
    total_actifs = Patient.objects.filter(medecin=request.user, actif=True).count()
    alertes = []
    for p in Patient.objects.filter(medecin=request.user, actif=True):
        derniere = p.derniere_consultation
        if derniere and derniere.interpretation.alerte_urgente:
            alertes.append(p)

    context = {
        "patients": patients,
        "q": q,
        "filtre": filtre,
        "total_actifs": total_actifs,
        "nb_alertes": len(alertes),
        "patients_alerte": alertes[:5],
    }
    return render(request, "patients/liste.html", context)


class PatientDetailView(LoginRequiredMixin, MedecinOwnedQuerysetMixin, DetailView):
    model = Patient
    template_name = "patients/detail.html"
    context_object_name = "patient"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        consultations = patient.consultations.order_by("-date_consultation")
        context["consultations"] = consultations
        context["prochains_rdv"] = patient.rendez_vous.filter(
            annule=False
        ).order_by("date_heure")

        # Données pour le graphique d'évolution INR (ordre chronologique)
        chrono = list(consultations.order_by("date_consultation"))
        context["graph_labels"] = [c.date_consultation.strftime("%d/%m/%y") for c in chrono]
        context["graph_valeurs"] = [float(c.valeur_inr) for c in chrono]
        context["cible_min"] = float(patient.inr_cible_min)
        context["cible_max"] = float(patient.inr_cible_max)
        return context


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/form.html"

    def form_valid(self, form):
        form.instance.medecin = self.request.user
        messages.success(self.request, f"Fiche patient créée pour {form.instance}.")
        return super().form_valid(form)


class PatientUpdateView(LoginRequiredMixin, MedecinOwnedQuerysetMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = "patients/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Fiche patient mise à jour.")
        return super().form_valid(form)


class PatientDeleteView(LoginRequiredMixin, MedecinOwnedQuerysetMixin, DeleteView):
    model = Patient
    template_name = "patients/confirmer_suppression.html"
    success_url = reverse_lazy("patients:liste")

    def form_valid(self, form):
        messages.success(self.request, "Fiche patient supprimée.")
        return super().form_valid(form)
