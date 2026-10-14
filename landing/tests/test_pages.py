import html
from pathlib import Path

import pytest

from app.content import VARIANTS, commun
from app.demo.route_geometry import demo_view
from app.offer import PLACES_EARLY_ACCESS
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


def test_waitlist_thank_you_does_not_promise_early_access_price(client):
    text = page(client, "/merci?attente=1")
    assert commun.MERCI_ATTENTE in text
    assert commun.MERCI_TEXTE not in text


@pytest.mark.parametrize("slug", list(VARIANTS))
def test_demo_is_rendered_in_final_state_without_js(client, slug):
    view = demo_view(VARIANTS[slug].demo)
    text = page(client, VARIANTS[slug].path)

    assert "data-demo" in text
    assert f'd="{view.path_apres}"' in text
    assert view.sms in text
    assert view.incident_label in text
    for marker in view.markers:
        tag = f'data-marker="{marker.key}"'
        assert tag in text
        hidden = 'opacity="0"' in text.split(tag, 1)[1].split(">", 1)[0]
        assert hidden == (marker.heure_apres is None), marker.key


def test_scripts_load_motion_first_and_deferred(client):
    text = page(client, "/")
    order = [text.index(f'src="/static/js/{name}" defer') for name in ("vendor/motion.js", "demo.js", "route-scroll.js", "lead-form.js")]
    assert order == sorted(order)


def test_reached_stops_are_visible_without_js_and_no_side_thread(client):
    text = page(client, "/")
    assert "data-route-thread" not in text
    assert text.count('data-route-stop class="route-stop is-reached"') == 4


def test_each_pain_card_shows_its_icon(client):
    text = page(client, "/infirmier")
    assert text.count('<svg class="size-7 text-principale"') >= 3


def test_yearly_saving_is_final_without_js(client):
    assert 'data-count-to="294" data-count-final="294">294</span>' in page(client, "/")
    assert 'data-count-to="354" data-count-final="354">354</span>' in page(client, "/infirmier")


def test_nurse_page_shows_ttc_prices_only(client):
    nurse = commun.offre("TTC")
    text = page(client, "/infirmier")
    assert nurse.prix_early in text and nurse.mention_taxe in text
    assert " € HT" not in text
    assert commun.offre("HT").prix_early in page(client, "/laveur-vitres")


def test_place_dots_show_taken_places(client, repository, lead_payload):
    repository.add(LeadIn.model_validate(lead_payload))
    text = page(client, "/")
    assert text.count("data-place-dot") == PLACES_EARLY_ACCESS
    assert text.count("data-place-taken") == 1


def test_place_dots_are_all_taken_when_full(settings):
    from fastapi.testclient import TestClient

    from app.factory import create_app

    class FullRepository(InMemoryLeadRepository):
        def count(self) -> int:
            return 42

    text = TestClient(create_app(settings, FullRepository())).get("/").text
    assert text.count("data-place-taken") == PLACES_EARLY_ACCESS


def test_thank_you_page_traces_the_logo(client):
    text = page(client, "/merci")
    assert 'class="logo mx-auto block size-28"' in text


def test_templates_use_only_manrope():
    for template in TEMPLATES.glob("*.html"):
        assert "font-douleur" not in template.read_text(), template.name


@pytest.mark.parametrize("path", [variant.path for variant in VARIANTS.values()] + ["/merci", "/confidentialite"])
def test_tagline_sits_with_the_logo_in_the_header(client, path):
    text = page(client, path)
    header = text[text.index("<header") : text.index("</header>")]
    assert "data-tagline" in header
    assert TAGLINE in header.split("data-tagline", 1)[1]
    assert text.count("data-tagline") == 1
