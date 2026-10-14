from decimal import Decimal

import pytest

from app.content import VARIANTS, commun
from app.rentabilite import COUT_CARBURANT_PAR_KM, Hypotheses, gains


def test_monthly_gains_from_fuel_admin_time_and_no_show():
    result = gains(Hypotheses(km_par_semaine=30, heures_admin_par_mois=2, no_show_par_mois=1, valeur_passage=Decimal("40")))

    assert (result.essence, result.administratif, result.no_show) == (18, 50, 40)
    assert result.total == 108


def test_fuel_cost_comes_from_2_euros_per_litre_at_7_litres_per_100_km():
    assert COUT_CARBURANT_PAR_KM == Decimal("0.14")


@pytest.mark.parametrize(
    "slug,total",
    [("generique", 108), ("laveur-vitres", 158), ("infirmier", 123), ("services-domicile", 100)],
)
def test_each_persona_has_its_own_estimate(slug, total):
    assert gains(VARIANTS[slug].rentabilite).total == total


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_estimate_covers_the_full_price_not_only_the_early_access_price(slug):
    variant = VARIANTS[slug]
    prix_plein = commun.offre(variant.taxe).prix_normal
    assert gains(variant.rentabilite).total > int(prix_plein.split(" ")[0].split(",")[0])


def test_hypothesis_lines_agree_in_number():
    lines = commun.lignes_rentabilite(
        Hypotheses(km_par_semaine=25, heures_admin_par_mois=2, no_show_par_mois=1, valeur_passage=Decimal("35"))
    )
    assert lines == (
        "25 km évités par semaine grâce au bon ordre de passage",
        "2 h de coups de fil et de planning en moins par mois",
        "1 déplacement pour rien évité par mois, grâce au SMS de confirmation la veille",
    )
    assert commun.lignes_rentabilite(
        Hypotheses(km_par_semaine=30, heures_admin_par_mois=3, no_show_par_mois=2, valeur_passage=Decimal("12"))
    )[2] == "2 déplacements pour rien évités par mois, grâce au SMS de confirmation la veille"
