from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from patients.models import Patient

from .forms import ConsultationForm, RendezVousForm
from .models import Consultation, RendezVous


@login_required
def agenda(request):
    """Vue agenda : liste des rendez-vous à venir (et récents) du médecin connecté."""
    maintenant = timezone.now()

    rendez_vous_a_venir = RendezVous.objects.filter(
        medecin=request.user,
        annule=False,
        date_heure__gte=maintenant,
    ).order_by("date_heure")

    rendez_vous_passes = RendezVous.objects.filter(
        medecin=request.user,
        date_heure__lt=maintenant,
    ).order_by("-date_heure")[:20]

    context = {
        "rendez_vous_a_venir": rendez_vous_a_venir,
        "rendez_vous_passes": rendez_vous_passes,
    }
    return render(request, "consultations/agenda.html", context)


@login_required
def creer_consultation(request, patient_pk):
    """Créer une nouvelle consultation pour un patient donné."""
    patient = get_object_or_404(Patient, pk=patient_pk, medecin=request.user)

    derniere = patient.derniere_consultation
    dose_precedente = derniere.dose_comprimes if derniere else None

    if request.method == "POST":
        form = ConsultationForm(request.POST, dose_precedente=dose_precedente)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.medecin = request.user
            consultation.save()
            messages.success(request, "Consultation enregistrée.")
            return redirect("consultations:detail", pk=consultation.pk)
    else:
        initial = {}
        if dose_precedente is not None:
            initial["dose_comprimes"] = dose_precedente
        form = ConsultationForm(initial=initial, dose_precedente=dose_precedente)

    context = {
        "form": form,
        "patient": patient,
    }
    return render(request, "consultations/form.html", context)


@login_required
def detail_consultation(request, pk):
    """Affiche le détail d'une consultation (INR, dose, interprétation, alertes)."""
    consultation = get_object_or_404(Consultation, pk=pk, medecin=request.user)
    patient = consultation.patient
    interpretation = consultation.interpretation

    # Positionnement de la jauge INR sur une échelle graduée de 0 à 5+
    echelle_max = 5
    valeur = float(consultation.valeur_inr)
    cible_min = float(patient.inr_cible_min)
    cible_max = float(patient.inr_cible_max)

    p_valeur = min(valeur / echelle_max, 1) * 100
    p_cible_min = min(cible_min / echelle_max, 1) * 100
    p_cible_max = min(cible_max / echelle_max, 1) * 100

    context = {
        "consultation": consultation,
        "patient": patient,
        "interpretation": interpretation,
        "p_valeur": round(p_valeur, 1),
        "p_cible_min": round(p_cible_min, 1),
        "p_cible_max": round(p_cible_max, 1),
    }
    return render(request, "consultations/detail.html", context)


@login_required
def creer_rendez_vous(request, patient_pk):
    """Créer un nouveau rendez-vous pour un patient donné."""
    patient = get_object_or_404(Patient, pk=patient_pk, medecin=request.user)

    if request.method == "POST":
        form = RendezVousForm(request.POST)
        if form.is_valid():
            rdv = form.save(commit=False)
            rdv.patient = patient
            rdv.medecin = request.user
            rdv.save()
            messages.success(request, "Rendez-vous programmé.")
            return redirect("consultations:rdv_detail", pk=rdv.pk)
    else:
        form = RendezVousForm()

    context = {
        "form": form,
        "patient": patient,
    }
    return render(request, "consultations/rdv_form.html", context)


@login_required
def detail_rendez_vous(request, pk):
    """Affiche le détail d'un rendez-vous."""
    rdv = get_object_or_404(RendezVous, pk=pk, medecin=request.user)
    context = {
        "rdv": rdv,
        "patient": rdv.patient,
    }
    return render(request, "consultations/rdv_detail.html", context)


@login_required
def modifier_rendez_vous(request, pk):
    """Modifier un rendez-vous existant."""
    rdv = get_object_or_404(RendezVous, pk=pk, medecin=request.user)

    if request.method == "POST":
        form = RendezVousForm(request.POST, instance=rdv)
        if form.is_valid():
            form.save()
            messages.success(request, "Rendez-vous mis à jour.")
            return redirect("consultations:rdv_detail", pk=rdv.pk)
    else:
        form = RendezVousForm(instance=rdv)

    context = {
        "form": form,
        "patient": rdv.patient,
        "rdv": rdv,
    }
    return render(request, "consultations/rdv_form.html", context)