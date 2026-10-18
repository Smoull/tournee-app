import pytest

from app.content import VARIANTS, commun
from app.rentabilite import Hypotheses, gain_temps_par_mois


def test_two_hours_per_week_over_four_weeks_at_25_euros_per_hour_are_worth_200_euros():
    assert gain_temps_par_mois(Hypotheses(heures_par_semaine=2)) == 200


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_every_persona_saves_two_hours_per_week(slug):
    assert VARIANTS[slug].rentabilite.heures_par_semaine == 2


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_time_saved_alone_covers_the_full_price(slug):
    variant = VARIANTS[slug]
    prix_plein = commun.offre(variant.taxe).prix_normal
    assert gain_temps_par_mois(variant.rentabilite) > int(prix_plein.split(" ")[0].split(",")[0])


def test_profitability_items_are_qualitative_without_figures():
    assert commun.postes_rentabilite("patients") == (
        ("Économie d'essence", "Le bon ordre de passage évite les kilomètres inutiles.", "gas-pump"),
        ("Gain de temps", "Moins d'appels et de planning à refaire chaque semaine.", "watch"),
        ("Absences anticipées des patients", "Le SMS envoyé la veille évite les déplacements inutiles.", "calendar-x"),
    )


def test_gain_is_announced_as_an_estimate_not_a_promise():
    assert commun.montant_gain(Hypotheses(heures_par_semaine=2)) == "Environ 200 €"


def test_estimate_is_labelled_as_a_theoretical_calculation_on_time_only():
    assert commun.RENTABILITE_MENTION == "Calcul théorique sur la base de 25 euros de l'heure, à adapter à votre activité."
    assert commun.RENTABILITE_GAIN == "gagnés par mois, rien qu'en temps (calcul théorique)"
    assert commun.RENTABILITE_LIAISON == "pour"
    assert commun.RENTABILITE_CHUTE == "Rien qu'avec le temps gagné, votre abonnement est remboursé."
