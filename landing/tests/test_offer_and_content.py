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
    return collect_strings(module_values) + collect_strings(list(VARIANTS.values())) + [commun.compteur(n) for n in (0, 1, 5)]


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
    assert commun.compteur(5) == "Plus que 5 places au tarif early access."
    assert commun.compteur(1) == "Plus qu'une place au tarif early access."
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


def test_nurse_variant_mentions_no_health_data():
    texts = " ".join(collect_strings(VARIANTS["infirmier"])).lower()
    assert not [word for word in HEALTH_WORDS if word in texts]


def test_prices_are_always_ht():
    for text in all_copy():
        for match in re.finditer(r"\d+ €", text):
            assert text[match.end() : match.end() + 3] == " HT", text


EXPECTED_SMS = {
    "generique": "Bonjour, votre passage est décalé à 10h15. Bouclé.tech",
    "laveur-vitres": "Bonjour, nous pouvons passer plus tôt : 7h00. Bouclé.tech",
    "infirmier": "Bonjour, mon passage chez vous est avancé à 9h00. Bouclé.tech",
    "services-domicile": "Bonjour, votre passage est décalé à 15h00. Bouclé.tech",
}


@pytest.mark.parametrize("slug", list(EXPECTED_SMS))
def test_each_variant_demo_sends_the_expected_sms(slug):
    assert sms_text(VARIANTS[slug].demo) == EXPECTED_SMS[slug]


def test_every_icon_used_in_content_is_vendored():
    used = [pain.icone for variant in VARIANTS.values() for pain in variant.douleurs]
    used += [item[2] for item in commun.FAISABILITE + commun.MORALE]
    assert set(used) <= set(ICONS)


def test_yearly_saving_is_split_for_the_counter_animation():
    assert commun.ECONOMIE_MONTANT == offer.format_euros(offer.economie_annuelle_ht())
    assert commun.ECONOMIE_AVANT + commun.ECONOMIE_MONTANT + commun.ECONOMIE_APRES == (
        "-24,50 € HT/mois à vie, soit 294 € HT économisés chaque année."
    )


def test_demo_copy_follows_copy_rules():
    for variant in VARIANTS.values():
        for text in (variant.demo.incident.label, sms_text(variant.demo)):
            assert "—" not in text
            assert not TUTOIEMENT.search(text)
    nurse = (VARIANTS["infirmier"].demo.incident.label + sms_text(VARIANTS["infirmier"].demo)).lower()
    assert not [word for word in HEALTH_WORDS if word in nurse]
