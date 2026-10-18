import re
from dataclasses import fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import get_args

import pytest

from app import offer
from app.content import VARIANTS, commun, legal
from app.demo.route_geometry import sms_text
from app.lead_schema import Douleur, Metier, Taille, Variante
from tools.vendor_assets import ICONS

TEMPLATES = Path(__file__).parent.parent / "app" / "templates"
TUTOIEMENT = re.compile(r"\b(tu|ton|ta|tes|toi|t'as)\b", re.IGNORECASE)
HEALTH_WORDS = ("soin", "patholog", "traitement", "médicament", "ordonnance", "diagnostic", "maladie")


def collect_strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if is_dataclass(value):
        return [text for field in fields(value) for text in collect_strings(getattr(value, field.name))]
    if isinstance(value, dict):
        return [text for item in value.items() for text in collect_strings(item)]
    if isinstance(value, (tuple, list)):
        return [text for item in value for text in collect_strings(item)]
    return []


def all_copy() -> list[str]:
    modules = [commun, legal]
    module_values = [value for module in modules for name, value in vars(module).items() if name.isupper()]
    offres = [commun.offre("HT"), commun.offre("TTC")]
    return (
        collect_strings(module_values)
        + collect_strings(list(VARIANTS.values()))
        + collect_strings(offres)
        + [commun.compteur(n) for n in (0, 1, 5)]
    )


def test_price_is_49_with_lifetime_half_price_early_access():
    assert offer.PRIX_HT == Decimal("49")
    assert offer.PRIX_EARLY_ACCESS_HT == Decimal("24.50")


def test_yearly_saving_is_294():
    assert offer.economie_annuelle_ht() == Decimal("294")


@pytest.mark.parametrize("montant,attendu", [(Decimal("49"), "49"), (Decimal("24.50"), "24,50"), (Decimal("294"), "294")])
def test_euros_are_written_the_french_way(montant, attendu):
    assert offer.format_euros(montant) == attendu


@pytest.mark.parametrize("inscrits,attendu", [(0, 10), (3, 7), (10, 0), (25, 0)])
def test_remaining_places_never_negative(inscrits, attendu):
    assert offer.places_restantes(inscrits) == attendu


def test_counter_wording():
    assert commun.compteur(5) == "Plus que 5 places en accès anticipé."
    assert commun.compteur(1) == "Plus qu'une place en accès anticipé."
    assert "0" not in commun.compteur(0)


def test_every_variant_route_has_complete_content():
    assert set(VARIANTS) == set(get_args(Variante))
    for slug, variant in VARIANTS.items():
        assert variant.slug == slug
        assert variant.path.startswith("/")
        assert variant.h1 and variant.sous_titre
        assert len(variant.douleurs) == 3
        assert all(pain.probleme and pain.solution for pain in variant.douleurs)
        assert variant.metier_prefill is None or variant.metier_prefill in get_args(Metier)
    assert len({variant.path for variant in VARIANTS.values()}) == len(VARIANTS)


def test_form_options_match_schema():
    assert [value for value, _ in commun.METIERS] == list(get_args(Metier))
    assert [value for value, _ in commun.TAILLES] == list(get_args(Taille))
    assert [value for value, _ in commun.DOULEURS] == list(get_args(Douleur))


def test_copy_uses_vouvoiement_and_no_em_dash():
    template_texts = [path.read_text() for path in TEMPLATES.glob("*.html")]
    for text in all_copy() + template_texts:
        assert "—" not in text, text
        assert not TUTOIEMENT.search(text), text


def test_copy_names_the_product_boucle_tech():
    for text in all_copy():
        assert not re.search(r"Bouclé(?!\.tech)", text), text


def test_nurse_variant_mentions_no_health_data():
    texts = " ".join(collect_strings(VARIANTS["infirmier"])).lower()
    assert not [word for word in HEALTH_WORDS if word in texts]


def test_prices_always_state_ht_or_ttc():
    for text in all_copy():
        for match in re.finditer(r"\d+ €", text):
            following = text[match.end() : match.end() + 4]
            assert following.startswith(" HT") or following == " TTC", text


def test_nurse_price_is_a_round_59_ttc():
    assert offer.PRIX_TTC == Decimal("59")


def test_only_nurses_see_ttc_prices():
    # Les actes infirmiers sont exonérés de TVA (art. 261-4-1° CGI) : ils ne la récupèrent pas, le TTC est leur vrai coût.
    assert {slug: variant.taxe for slug, variant in VARIANTS.items()} == {
        "generique": "HT",
        "laveur-vitres": "HT",
        "infirmier": "TTC",
        "services-domicile": "HT",
    }


EXPECTED_SMS = {
    "generique": "Bonjour, votre passage est décalé à 10h15. Bouclé.tech",
    "laveur-vitres": "Bonjour, nous pouvons passer plus tôt : 7h00. Bouclé.tech",
    "infirmier": "Bonjour M. Martin, mon passage chez vous est avancé à 9h00. Votre infirmière, Florence.",
    "services-domicile": "Bonjour, votre passage est décalé à 15h00. Bouclé.tech",
}


@pytest.mark.parametrize("slug", list(EXPECTED_SMS))
def test_each_variant_demo_sends_the_expected_sms(slug):
    assert sms_text(VARIANTS[slug].demo) == EXPECTED_SMS[slug]


def test_every_icon_used_in_content_is_vendored():
    used = [pain.icone for variant in VARIANTS.values() for pain in variant.douleurs]
    used += [item[2] for variant in VARIANTS.values() for item in commun.faisabilite(variant.support_tournee)]
    used += [item[2] for item in commun.morale("clients", commun.CONFORMITE_RGPD)]
    assert set(used) <= set(ICONS)


@pytest.mark.parametrize(
    "taxe,prix_normal,prix_early,economie,nombre",
    [
        ("HT", "49 € HT/mois", "24,50 € HT/mois à vie", "-24,50 € HT/mois à vie, soit 294 € HT économisés chaque année.", "294"),
        ("TTC", "59 € TTC/mois", "29,50 € TTC/mois à vie", "-29,50 € TTC/mois à vie, soit 354 € TTC économisés chaque année.", "354"),
    ],
)
def test_offer_texts_follow_the_tax_display(taxe, prix_normal, prix_early, economie, nombre):
    texts = commun.offre(taxe)
    assert texts.prix_normal == prix_normal
    assert texts.prix_early == prix_early
    assert texts.economie_avant + texts.economie_montant + texts.economie_apres == economie
    assert texts.economie_nombre == nombre


def test_checkboxes_say_clearly_what_each_one_allows():
    assert commun.ACCEPTE_APPEL == "Oui, appelez-moi 15 minutes pour parler de ma tournée (facultatif)."
    assert commun.CONSENTEMENT == (
        "J'accepte que Bouclé.tech conserve ces informations pour me prévenir de l'ouverture de l'accès anticipé."
    )


def test_demo_copy_follows_copy_rules():
    for variant in VARIANTS.values():
        for text in (variant.demo.incident.label, sms_text(variant.demo)):
            assert "—" not in text
            assert not TUTOIEMENT.search(text)
    nurse = (VARIANTS["infirmier"].demo.incident.label + sms_text(VARIANTS["infirmier"].demo)).lower()
    assert not [word for word in HEALTH_WORDS if word in nurse]


def test_copy_says_acces_anticipe_not_early_access():
    template_texts = [path.read_text() for path in TEMPLATES.glob("*.html")]
    for text in all_copy() + template_texts:
        assert "early access" not in text.lower(), text


def test_feasibility_promises_expert_onboarding_and_paper_or_calendar():
    faisabilite = commun.faisabilite(VARIANTS["laveur-vitres"].support_tournee)
    assert faisabilite[0][:2] == (
        "Prise en main accompagnée par un expert.",
        "On configure le logiciel avec vous.",
    )
    assert faisabilite[1][:2] == (
        "Votre tournée sur papier ou dans votre agenda.",
        "Un PDF clair chaque matin, ou directement dans votre agenda numérique.",
    )


def test_nurse_feasibility_shares_the_planning_with_the_practice():
    assert commun.faisabilite(VARIANTS["infirmier"].support_tournee)[1] == (
        "Un planning partagé avec tout le cabinet.",
        "Un remplacement d'un confrère, un imprévu : mise à jour de l'agenda automatique.",
        "calendar-check",
    )


def test_profitability_first_item_speaks_of_fuel_savings():
    assert commun.postes_rentabilite("clients")[0][::2] == ("Économie d'essence", "gas-pump")


def test_profitability_second_item_speaks_of_time_saved():
    assert commun.postes_rentabilite("clients")[1][::2] == ("Gain de temps", "watch")


def test_no_show_item_shows_a_crossed_calendar():
    assert commun.postes_rentabilite("patients")[2][::2] == ("Absences anticipées des patients", "calendar-x")


def test_feasibility_keeps_the_user_in_control():
    assert commun.faisabilite(commun.SUPPORT_TOURNEE)[2][:2] == (
        "Vous gardez la main.",
        "Chaque tournée proposée peut être validée ou ajustée en un geste.",
    )


def test_offer_title_says_nothing_to_pay_today():
    assert commun.ACCES_ANTICIPE.titre == "Accès anticipé : rien à payer aujourd'hui"


def test_no_commitment_is_stated_once_as_its_own_line():
    assert commun.ACCES_ANTICIPE.sans_engagement == "Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui."
    assert "Sans engagement" not in commun.offre("HT").attente


def test_thank_you_fits_both_test_and_early_access_framings():
    assert commun.MERCI_TEXTE == "Votre demande est enregistrée. Si vous adoptez Bouclé.tech : -50 % à vie."
