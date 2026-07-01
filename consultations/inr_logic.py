"""
Logique d'interprétation de l'INR (International Normalized Ratio) et de
suggestion indicative de palier d'ajustement de dose.

IMPORTANT — Portée et limites :
Ce module fournit une AIDE À LA LECTURE de la valeur d'INR par rapport à la
cible définie par le médecin pour un patient donné, ainsi qu'une SUGGESTION
INDICATIVE de palier d'ajustement de dose (variation usuelle de ±10 à ±20 %).
Il ne constitue en aucun cas une décision médicale automatisée :
- La suggestion de palier n'est JAMAIS utilisée pour pré-remplir le champ de
  dose ; elle est affichée à titre d'aide, à côté du champ de saisie.
- Toute dose effectivement administrée est saisie et validée par le médecin.
- Tout changement de dose par rapport à la consultation précédente doit être
  motivé (champ obligatoire géré au niveau du formulaire de consultation).

La cible INR (inr_cible_min / inr_cible_max) est configurable par patient
car elle dépend du contexte clinique (ex. prothèse cardiaque mécanique).
"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass


@dataclass
class InterpretationINR:
    niveau: str          # "sous_cible" | "cible" | "sur_cible" | "alerte_urgente"
    libelle: str          # court résumé affiché en badge
    message: str          # explication détaillée
    couleur: str          # nom de classe CSS pour l'affichage (info/success/warning/danger)
    alerte_urgente: bool  # True si seuil de danger franchi (hémorragique OU sous-dosage critique)
    avis_medecin_hospitalisation: bool = False  # True = urgence nécessitant hospitalisation


def interpreter_inr(
    valeur_inr,
    inr_cible_min,
    inr_cible_max,
    saignement_signale=False,
    porteur_prothese_mecanique=False,
):
    """
    Détermine le niveau de risque d'une valeur d'INR par rapport à la cible
    configurée pour le patient, et renvoie un message d'aide à la lecture.

    :param valeur_inr: Decimal ou float, valeur mesurée de l'INR.
    :param inr_cible_min: borne basse de la cible pour ce patient.
    :param inr_cible_max: borne haute de la cible pour ce patient.
    :param saignement_signale: bool, si un événement hémorragique a été signalé.
    :param porteur_prothese_mecanique: bool, si le patient porte une prothèse
        cardiaque mécanique. Abaisse le seuil d'alerte de sous-dosage, car un
        INR trop bas expose alors à un risque de thrombose de prothèse —
        une urgence au même titre qu'un risque hémorragique élevé.
    :return: InterpretationINR
    """
    valeur = Decimal(str(valeur_inr))
    cible_min = Decimal(str(inr_cible_min))
    cible_max = Decimal(str(inr_cible_max))

    # --- Alerte urgente : événement hémorragique signalé, quel que soit l'INR ---
    if saignement_signale:
        return InterpretationINR(
            niveau="alerte_urgente",
            libelle="⚠ Événement hémorragique",
            message=(
                "Un événement hémorragique a été signalé pour cette consultation. "
                "Quelle que soit la valeur d'INR, ceci nécessite un contact "
                "médical rapide et une réévaluation immédiate du traitement."
            ),
            couleur="danger",
            alerte_urgente=True,
        )

    # --- Alerte urgente : INR extrêmement élevé — AVIS MÉDECIN avec probable
    #     hospitalisation pour ajustement thérapeutique en intra-hospitalier. ---
    if valeur > Decimal("5.0"):
        return InterpretationINR(
            niveau="alerte_urgente",
            libelle="⚠ AVIS MÉDECIN — Hospitalisation",
            message=(
                f"INR à {valeur} : risque hémorragique majeur. AVIS MÉDECIN "
                "nécessaire en urgence, avec hospitalisation probable pour "
                "ajustement thérapeutique en intra-hospitalier. Ne pas "
                "attendre la prochaine consultation programmée."
            ),
            couleur="danger",
            alerte_urgente=True,
            avis_medecin_hospitalisation=True,
        )

    # --- Alerte urgente : INR très élevé (seuil de danger hémorragique) ---
    if valeur > Decimal("4.0"):
        return InterpretationINR(
            niveau="alerte_urgente",
            libelle="⚠ INR très élevé — Urgence",
            message=(
                f"INR à {valeur} : seuil de risque hémorragique élevé franchi. "
                "Il est recommandé de contacter rapidement le médecin traitant "
                "pour réévaluation urgente du traitement. Ne pas modifier la "
                "dose sans avis médical."
            ),
            couleur="danger",
            alerte_urgente=True,
        )

    # --- Alerte urgente : sous-dosage important chez un porteur de prothèse
    #     mécanique — AVIS MÉDECIN avec probable hospitalisation, au même
    #     titre qu'un INR hémorragique majeur. ---
    if porteur_prothese_mecanique and valeur < (cible_min - Decimal("1.0")):
        return InterpretationINR(
            niveau="alerte_urgente",
            libelle="⚠ AVIS MÉDECIN — Hospitalisation",
            message=(
                f"INR à {valeur}, nettement sous la cible ({cible_min}–{cible_max}) "
                "chez un patient porteur d'une prothèse cardiaque mécanique. "
                "Ce sous-dosage expose à un risque de thrombose de prothèse. "
                "AVIS MÉDECIN nécessaire en urgence, avec hospitalisation "
                "probable pour ajustement thérapeutique en intra-hospitalier."
            ),
            couleur="danger",
            alerte_urgente=True,
            avis_medecin_hospitalisation=True,
        )

    # --- Sous la cible ---
    if valeur < cible_min:
        message = (
            f"INR à {valeur}, sous la cible définie ({cible_min}–{cible_max}). "
            "Le sang n'est pas suffisamment anticoagulé : risque accru de "
            "formation de caillot ou de récidive. La dose peut nécessiter "
            "une réévaluation médicale."
        )
        if porteur_prothese_mecanique:
            message += (
                " Chez ce patient porteur d'une prothèse mécanique, une "
                "surveillance rapprochée est particulièrement importante."
            )
        return InterpretationINR(
            niveau="sous_cible",
            libelle="INR sous la cible",
            message=message,
            couleur="warning",
            alerte_urgente=False,
        )

    # --- Dans la cible ---
    if cible_min <= valeur <= cible_max:
        return InterpretationINR(
            niveau="cible",
            libelle="INR dans la cible",
            message=(
                f"INR à {valeur}, dans la zone cible habituelle ({cible_min}–{cible_max}). "
                "Anticoagulation jugée adéquate avec un risque hémorragique "
                "généralement acceptable."
            ),
            couleur="success",
            alerte_urgente=False,
        )

    # --- Au-dessus de la cible mais sous le seuil d'alerte critique ---
    return InterpretationINR(
        niveau="sur_cible",
        libelle="INR au-dessus de la cible",
        message=(
            f"INR à {valeur}, au-dessus de la cible définie ({cible_min}–{cible_max}). "
            "Risque de sur-anticoagulation et de saignement augmenté. "
            "Un avis médical est recommandé."
        ),
        couleur="warning",
        alerte_urgente=False,
    )


# --- Aide à la conversion de dose pour le Sintrom 4 mg (comprimé sécable) ---
# Rappel : ceci est un référentiel d'affichage, jamais une prescription automatique.
SINTROM_DOSES_COURANTES = [
    (Decimal("0.25"), "1/4 de comprimé", "1 mg"),
    (Decimal("0.5"), "1/2 comprimé", "2 mg"),
    (Decimal("0.75"), "3/4 de comprimé", "3 mg"),
    (Decimal("1.0"), "1 comprimé entier", "4 mg"),
    (Decimal("1.5"), "1 comprimé et 1/2", "6 mg"),
    (Decimal("2.0"), "2 comprimés", "8 mg"),
]


def comprimes_vers_mg_sintrom(nb_comprimes):
    """Convertit un nombre de comprimés de Sintrom 4 mg en mg (1 cp = 4 mg)."""
    return Decimal(str(nb_comprimes)) * Decimal("4")


@dataclass
class SuggestionAjustement:
    palier: str            # "hausse_forte" | "hausse_legere" | "maintien" | "baisse_legere" | "baisse_forte" | "indetermine"
    pourcentage: str        # ex : "+10 à 20 %", "0 %", "-10 à 20 %", ou "" si indéterminé
    libelle: str            # court résumé
    dose_suggeree_cp: object  # Decimal arrondi au quart de comprimé le plus proche, ou None
    message: str            # explication, toujours avec rappel de la portée indicative


def _arrondir_quart_comprime(valeur_decimale):
    """Arrondit une dose en comprimés au quart de comprimé le plus proche (0.25)."""
    quart = Decimal("0.25")
    return (valeur_decimale / quart).to_integral_value(rounding=ROUND_HALF_UP) * quart


def suggerer_ajustement_dose(
    valeur_inr,
    inr_cible_min,
    inr_cible_max,
    dose_actuelle_cp,
    saignement_signale=False,
):
    """
    Calcule une SUGGESTION INDICATIVE de palier d'ajustement de dose, à partir
    de l'écart entre l'INR mesuré et la cible du patient, selon des règles de
    paliers usuelles (variation de ±10 à ±20 % de la dose hebdomadaire totale,
    ici appliquée à la dose journalière en comprimés de Sintrom 4 mg).

    IMPORTANT : cette fonction ne décide rien. Elle ne doit jamais être
    utilisée pour pré-remplir automatiquement le champ de dose. Le médecin
    reste seul décisionnaire de la dose réellement prescrite, et doit motiver
    tout changement de dose par rapport à la consultation précédente.

    :param valeur_inr: Decimal ou float, valeur mesurée de l'INR.
    :param inr_cible_min: borne basse de la cible pour ce patient.
    :param inr_cible_max: borne haute de la cible pour ce patient.
    :param dose_actuelle_cp: Decimal ou float, dose actuelle en comprimés/jour.
    :param saignement_signale: bool, si un événement hémorragique a été signalé.
    :return: SuggestionAjustement
    """
    valeur = Decimal(str(valeur_inr))
    cible_min = Decimal(str(inr_cible_min))
    cible_max = Decimal(str(inr_cible_max))
    dose_actuelle = Decimal(str(dose_actuelle_cp)) if dose_actuelle_cp is not None else None

    if dose_actuelle is None:
        return SuggestionAjustement(
            palier="indetermine",
            pourcentage="",
            libelle="Dose actuelle inconnue",
            dose_suggeree_cp=None,
            message="Aucune dose de référence connue pour calculer une suggestion de palier.",
        )

    # En cas d'événement hémorragique, on ne propose pas de palier de
    # variation : la priorité est l'avis médical urgent, pas un ajustement
    # de routine.
    if saignement_signale:
        return SuggestionAjustement(
            palier="indetermine",
            pourcentage="",
            libelle="Avis médical requis",
            dose_suggeree_cp=None,
            message=(
                "Un événement hémorragique a été signalé : aucune suggestion "
                "de palier n'est proposée. La conduite à tenir doit être "
                "déterminée par le médecin, en urgence si nécessaire."
            ),
        )

    ecart_min = cible_min - valeur   # > 0 si sous la cible
    ecart_max = valeur - cible_max   # > 0 si au-dessus de la cible

    if valeur > Decimal("4.0") or (ecart_min > Decimal("1.0")):
        # Écarts importants (très haut ou très bas) : on signale qu'un palier
        # usuel n'est pas adapté, la situation relevant d'une réévaluation
        # médicale au cas par cas plutôt que d'un ajustement de routine.
        palier = "baisse_forte" if valeur > Decimal("4.0") else "hausse_forte"
        pourcentage = "-10 à -20 %" if palier == "baisse_forte" else "+10 à +20 %"
        facteur = Decimal("0.85") if palier == "baisse_forte" else Decimal("1.15")
        dose_suggeree = _arrondir_quart_comprime(dose_actuelle * facteur)
        if palier == "hausse_forte" and dose_suggeree <= dose_actuelle:
            dose_suggeree = dose_actuelle + Decimal("0.25")
        elif palier == "baisse_forte" and dose_suggeree >= dose_actuelle:
            dose_suggeree = max(Decimal("0"), dose_actuelle - Decimal("0.25"))
        return SuggestionAjustement(
            palier=palier,
            pourcentage=pourcentage,
            libelle="Écart important — palier usuel + avis médical",
            dose_suggeree_cp=dose_suggeree,
            message=(
                f"Écart important par rapport à la cible ({cible_min}–{cible_max}). "
                f"À titre indicatif, un palier usuel correspondrait à une variation "
                f"de dose de {pourcentage}, soit environ {dose_suggeree} cp/jour. "
                "Compte tenu de l'ampleur de l'écart, un avis médical rapide est "
                "recommandé avant toute modification."
            ),
        )

    if ecart_min > Decimal("0.3"):
        facteur = Decimal("1.10")
        dose_suggeree = _arrondir_quart_comprime(dose_actuelle * facteur)
        if dose_suggeree <= dose_actuelle:
            dose_suggeree = dose_actuelle + Decimal("0.25")
        return SuggestionAjustement(
            palier="hausse_legere",
            pourcentage="+10 %",
            libelle="Palier indicatif : légère hausse",
            dose_suggeree_cp=dose_suggeree,
            message=(
                f"INR sous la cible ({cible_min}–{cible_max}). À titre indicatif, "
                f"un palier usuel correspondrait à une hausse d'environ 10 % de "
                f"la dose, soit environ {dose_suggeree} cp/jour."
            ),
        )

    if ecart_max > Decimal("0.3"):
        facteur = Decimal("0.90")
        dose_suggeree = _arrondir_quart_comprime(dose_actuelle * facteur)
        if dose_suggeree >= dose_actuelle:
            dose_suggeree = max(Decimal("0"), dose_actuelle - Decimal("0.25"))
        return SuggestionAjustement(
            palier="baisse_legere",
            pourcentage="-10 %",
            libelle="Palier indicatif : légère baisse",
            dose_suggeree_cp=dose_suggeree,
            message=(
                f"INR au-dessus de la cible ({cible_min}–{cible_max}). À titre "
                f"indicatif, un palier usuel correspondrait à une baisse "
                f"d'environ 10 % de la dose, soit environ {dose_suggeree} cp/jour."
            ),
        )

    return SuggestionAjustement(
        palier="maintien",
        pourcentage="0 %",
        libelle="Palier indicatif : maintien",
        dose_suggeree_cp=dose_actuelle,
        message=(
            f"INR proche ou dans la cible ({cible_min}–{cible_max}). À titre "
            f"indicatif, un maintien de la dose actuelle ({dose_actuelle} cp/jour) "
            "serait usuel."
        ),
    )