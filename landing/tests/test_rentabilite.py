import pytest

from app.content import VARIANTS, commun
from app.rentabilite import Hypotheses, gain_temps_par_mois


def test_two_hours_per_week_over_four_weeks_at_25_euros_per_hour_are_worth_200_euros():
    assert gain_temps_par_mois(Hypotheses(km_par_semaine=30, heures_par_semaine=2, no_show_par_mois=1)) == 200


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_every_persona_saves_two_hours_per_week(slug):
    assert VARIANTS[slug].rentabilite.heures_par_semaine == 2


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_time_saved_alone_covers_the_full_price(slug):
    variant = VARIANTS[slug]
    prix_plein = commun.offre(variant.taxe).prix_normal
    assert gain_temps_par_mois(variant.rentabilite) > int(prix_plein.split(" ")[0].split(",")[0])


def test_cards_show_km_time_value_and_avoided_trips():
    cartes = commun.cartes_rentabilite(Hypotheses(km_par_semaine=40, heures_par_semaine=2, no_show_par_mois=2))
    assert cartes == (
        ("≈ 40 km", "évités chaque semaine grâce au bon ordre de passage"),
        ("200 €", "par mois, avec 2 h gagnées chaque semaine sur les appels et le planning"),
        ("≈ 2", "déplacements inutiles évités chaque mois, grâce au SMS envoyé la veille"),
    )


def test_single_avoided_trip_is_singular():
    cartes = commun.cartes_rentabilite(Hypotheses(km_par_semaine=25, heures_par_semaine=2, no_show_par_mois=1))
    assert cartes[2] == ("≈ 1", "déplacement inutile évité chaque mois, grâce au SMS envoyé la veille")


def test_estimate_is_labelled_as_a_theoretical_calculation_on_time_only():
    assert commun.RENTABILITE_MENTION == "Calcul théorique sur la base de 25 euros de l'heure, à adapter à votre activité."
    assert commun.RENTABILITE_GAIN == "gagnés par mois, rien qu'en temps (calcul théorique)"
    assert commun.RENTABILITE_CHUTE == "Rien qu'avec le temps gagné, votre abonnement est remboursé."
