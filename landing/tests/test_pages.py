import html
from pathlib import Path

import pytest

from app.content import VARIANTS, commun
from app.lead_repository import InMemoryLeadRepository
from app.lead_schema import LeadIn
from brand.export import SUFFIX_RATIO
from brand.identity import TAGLINE

TEMPLATES = Path(__file__).parent.parent / "app" / "templates"


def page(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, path
    return html.unescape(response.text)


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_each_variant_renders_its_fuom_content(client, slug):
    variant = VARIANTS[slug]
    text = page(client, variant.path)

    assert variant.h1 in text
    assert variant.sous_titre in text
    for pain in variant.douleurs:
        assert pain.probleme in text and pain.solution in text
    for block in (commun.FAISABILITE_TITRE, commun.MORALE_TITRE, commun.OPPORTUNITE_TITRE, commun.FORMULAIRE_TITRE):
        assert block in text
    assert f'name="variante" value="{slug}"' in text
    assert TAGLINE in text
    assert "/static/brand/og-image.png" in text


def test_variant_prefills_its_trade(client):
    assert '<option value="laveur-vitres" selected>' in page(client, "/laveur-vitres")
    generic = page(client, "/")
    assert '<option value="" disabled selected>' in generic
    assert not [value for value, _ in commun.METIERS if f'<option value="{value}" selected>' in generic]


def test_utm_parameters_are_carried_in_the_form(client):
    text = page(client, "/?utm_source=agence&utm_campaign=lancement")
    assert 'name="utm_source" value="agence"' in text
    assert 'name="utm_campaign" value="lancement"' in text


def test_utm_values_are_escaped(client):
    response = client.get('/?utm_source="><script>alert(1)</script>')
    assert "<script>alert(1)</script>" not in response.text


def test_counter_decreases_after_a_lead(client, repository, lead_payload):
    assert commun.compteur(10) in page(client, "/")
    repository.add(LeadIn.model_validate(lead_payload))
    assert commun.compteur(9) in page(client, "/")


def test_counter_never_goes_negative(settings):
    from fastapi.testclient import TestClient

    from app.factory import create_app

    class FullRepository(InMemoryLeadRepository):
        def count(self) -> int:
            return 42

    text = html.unescape(TestClient(create_app(settings, FullRepository())).get("/").text)
    assert commun.compteur(0) in text


def test_thank_you_page_links_to_calcom(client):
    text = page(client, "/merci")
    assert commun.MERCI_TITRE in text
    assert 'href="https://cal.com/example/15min"' in text


@pytest.mark.parametrize("path", ["/mentions-legales", "/confidentialite"])
def test_legal_pages_render(client, path):
    assert "Bouclé" in page(client, path)


def test_footer_has_unsubscribe_mail_link(client):
    assert 'href="mailto:contact@example.com?subject=Désinscription"' in page(client, "/")


def test_wordmark_suffix_class_matches_brand_ratio():
    assert f"text-[{SUFFIX_RATIO}em]" in (TEMPLATES / "base.html").read_text()


def test_templates_have_no_inline_script():
    for template in TEMPLATES.glob("*.html"):
        source = template.read_text()
        assert "<script>" not in source and "onclick=" not in source, template.name
