import re
from pathlib import Path

LANDING_DIR = Path(__file__).parent.parent
ROUTE_SCROLL = (LANDING_DIR / "static" / "js" / "route-scroll.js").read_text()
DEMO = (LANDING_DIR / "static" / "js" / "demo.js").read_text()
CSS = (LANDING_DIR / "app" / "static_src" / "input.css").read_text()


def test_reveals_never_wait_for_a_ratio_of_element_height():
    # Un seuil en ratio (amount: 0.3) n'est jamais atteint si l'élément dépasse l'écran
    # (zoom 400 %, paysage) : le contenu masqué par le JS resterait invisible pour toujours.
    assert not re.search(r"amount:\s*0?\.\d", ROUTE_SCROLL)


def test_demo_plays_once_per_entry_instead_of_looping_forever():
    # WCAG 2.2.2 : pas de mouvement automatique sans fin sans moyen de l'arrêter.
    assert "while (" not in DEMO


def test_no_infinite_css_animation():
    assert "infinite" not in CSS


def test_demo_pauses_off_screen_so_fast_scrollers_see_it_whole_on_return():
    assert ".pause()" in DEMO
    assert ".play()" in DEMO
