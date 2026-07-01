from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("", views.liste_patients, name="liste"),
    path("nouveau/", views.PatientCreateView.as_view(), name="creer"),
    path("<int:pk>/", views.PatientDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", views.PatientUpdateView.as_view(), name="modifier"),
    path("<int:pk>/supprimer/", views.PatientDeleteView.as_view(), name="supprimer"),
]
