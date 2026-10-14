import re
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import get_args

import pytest

from app import offer
from app.content import VARIANTS, commun, legal
from app.lead_schema import Douleur, Metier, Taille, Variante

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


def test_yearly_saving_is_120():
    assert offer.economie_annuelle_ht() == 120


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
