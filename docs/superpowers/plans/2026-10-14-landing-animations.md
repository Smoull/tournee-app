# Landing Bouclé.tech : animations et démo vivante, Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rendre la landing vendeuse : démo vivante par métier dans le hero, fil de la route qui se dessine au défilement, petits moments animés (cartes, prix, compteur, page merci), icônes Phosphor.

**Architecture:** Toute la logique (scénarios, heures, tracés SVG) est en Python, testée par pytest, et rendue côté serveur **à l'état final** dans le HTML (data-attributes). Le JS (`demo.js`, `route-scroll.js`) ne fait que jouer les animations avec Motion (UMD, servi localement). Motion et les icônes Phosphor sont téléchargés une fois par `tools/vendor_assets.py`, vérifiés par empreinte sha512, puis commités.

**Tech Stack:** Python 3.12, FastAPI/Jinja2 (existant), Motion 13.4.6 (MIT, UMD `window.Motion`), `@phosphor-icons/core` 2.1.1 (MIT, SVG `regular`), Tailwind v4.1.11 standalone, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-landing-animations-design.md` (complète `docs/superpowers/specs/2026-10-12-landing-validation-design.md`)

## Global Constraints

- Tout se lance via `uv run` depuis `landing/`. Pas de npm, pas de CDN : Motion et icônes servis depuis `static/`.
- TDD : test écrit et rouge avant le code (CLAUDE.md). Fail fast : icône inconnue, scénario invalide = exception explicite.
- Palette uniquement : fond `#F4F7F7`, texte `#11181C`, principale `#2A7A6B`, accent `#C67A10` (opacités autorisées, pas d'ombre noire, pas de 5e teinte). Icônes en `currentColor`.
- Polices : Manrope (tout sauf H1), Fraunces 600 (H1 et « C'est bouclé. » uniquement).
- Textes : vouvoiement, pas de tiret cadratin, prix HT ; aucune donnée ou mot de santé côté infirmier ; aucun nom de client dans la démo.
- `prefers-reduced-motion: reduce` ou JS absent : tout est visible à l'état final, sans mouvement. Les états cachés initiaux sont posés par le JS uniquement.
- Démo : 5 arrêts de départ, un arrêt toutes les **45 min** ; retrait → suivants avancent de 45 min ; ajout → suivants reculent de 45 min ; SMS = nouvelle heure du premier arrêt existant dont l'heure change, format `10h30` (sans zéro initial : `7h00`).
- Budget JS : ≤ 60 Ko **transférés** (gzip) au total. Motion pèse 143 Ko minifié / 49 Ko gzip (mesuré) ; la spec disait « 60 Ko minifié », corrigé en Task 6.
- Aucun script inline exécutable (CSP phase 2).

## Review Focus

1. **Écran très étroit (320 px)** : les heures de la démo et la bulle SMS restent lisibles, rien ne déborde horizontalement. → vérification capture 320 px en Task 6 (étape 5).
2. **JS absent ou bloqué** : la démo, les arrêts du fil, le prix et le compteur sont visibles à l'état final. → `test_demo_is_rendered_in_final_state_without_js` (Task 5).
3. **« Réduire les animations » activé** : aucune animation, état final affiché. → capture Chrome `--force-prefers-reduced-motion` en Task 6 (étape 5) + garde dans chaque script.
4. **Toutes les places prises** : 10 pastilles pleines, compteur « Toutes les places… », jamais de pastille négative. → `test_place_dots_are_all_taken_when_full` (Task 5).
5. **Démo hors écran puis revenue / clic sur Rejouer pendant la lecture** : une seule boucle active, pas d'animations superposées. → garde `running` + `looping` dans `demo.js` (Task 6), vérification manuelle humaine.

---

## File Structure

```
landing/
  tools/__init__.py, tools/vendor_assets.py   téléchargement + vérification sha512 (Motion, Phosphor)
  app/icons.py                                  icon(name, css_class) -> Markup (SVG local)
  app/demo/__init__.py
  app/demo/scenario.py                          Incident, DemoScenario, DemoStop (validation fail fast)
  app/demo/route_geometry.py                    stops_before/after, route_path, format_heure, sms_text, demo_view
  app/content/models.py                         Pain + icone, Variant + demo
  app/content/*.py                              scénarios + icônes par métier, ECONOMIE découpé
  app/templates/_demo.html                      démo (état final + data-attributes)
  app/templates/landing.html, merci.html, base.html
  app/static_src/icons/*.svg + LICENSE          (généré par vendor_assets, commité)
  app/static_src/input.css                      styles des arrêts, halo CTA
  static/js/vendor/motion.js + motion-LICENSE.md (généré, commité)
  static/js/demo.js, static/js/route-scroll.js
  tests/test_vendor_assets.py, test_icons.py, test_demo.py (+ ajouts test_offer_and_content.py, test_pages.py)
```

---

### Task 1: Outil de vendoring (Motion + Phosphor) avec vérification d'empreinte

**Files:**
- Create: `landing/tools/__init__.py`, `landing/tools/vendor_assets.py`
- Test: `landing/tests/test_vendor_assets.py`
- Generated (commités) : `landing/static/js/vendor/motion.js`, `landing/static/js/vendor/motion-LICENSE.md`, `landing/app/static_src/icons/*.svg`, `landing/app/static_src/icons/LICENSE`

**Interfaces:**
- Produces: `ICONS: tuple[str, ...]` (13 noms), `IntegrityError(RuntimeError)`, `verify_integrity(data: bytes, integrity: str) -> None`, `read_member(archive: bytes, member: str) -> bytes`, `vendor() -> None`, `ICONS_DIR = landing/app/static_src/icons`.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_vendor_assets.py` :

```python
import base64
import hashlib
import io
import tarfile

import pytest

from tools.vendor_assets import ICONS, IntegrityError, read_member, verify_integrity


def sha512_integrity(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def make_tgz(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(f"package/{name}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_matching_integrity_passes():
    verify_integrity(b"motion", sha512_integrity(b"motion"))


def test_tampered_archive_is_refused():
    with pytest.raises(IntegrityError):
        verify_integrity(b"motion modifie", sha512_integrity(b"motion"))


def test_non_sha512_integrity_is_refused():
    with pytest.raises(IntegrityError):
        verify_integrity(b"motion", "sha1-abc")


def test_read_member_returns_file_content_without_extracting_to_disk():
    archive = make_tgz({"dist/motion.js": b"window.Motion={}"})
    assert read_member(archive, "dist/motion.js") == b"window.Motion={}"


def test_read_member_missing_file_fails():
    with pytest.raises(KeyError):
        read_member(make_tgz({"a.js": b""}), "dist/motion.js")


def test_icon_list_is_closed_and_unique():
    assert len(ICONS) == len(set(ICONS)) == 13
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_vendor_assets.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Implémenter**

`landing/tools/__init__.py` : fichier vide.

`landing/tools/vendor_assets.py` :

```python
import base64
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

LANDING_DIR = Path(__file__).parent.parent
MOTION_DIR = LANDING_DIR / "static" / "js" / "vendor"
ICONS_DIR = LANDING_DIR / "app" / "static_src" / "icons"

# Versions figées ; empreintes copiées depuis le registre npm (champ dist.integrity).
MOTION = (
    "https://registry.npmjs.org/motion/-/motion-13.4.6.tgz",
    "sha512-zDXi6lIdyhda6wZlTsv9QgT2ed6UExAfRegtl/akQmZb5iaeLlArXr9Gmo/hx3iTx2y4R7tmdb9k9koFQmV+NQ==",
)
PHOSPHOR = (
    "https://registry.npmjs.org/@phosphor-icons/core/-/core-2.1.1.tgz",
    "sha512-v4ARvrip4qBCImOE5rmPUylOEK4iiED9ZyKjcvzuezqMaiRASCHKcRIuvvxL/twvLpkfnEODCOJp5dM4eZilxQ==",
)
ICONS = (
    "x-circle",
    "user-minus",
    "plus-circle",
    "lightning",
    "chat-text",
    "printer",
    "hand-heart",
    "shield-check",
    "clock-countdown",
    "calendar-check",
    "map-pin",
    "arrow-counter-clockwise",
    "cloud-rain",
)


class IntegrityError(RuntimeError):
    pass


def verify_integrity(data: bytes, integrity: str) -> None:
    algorithm, _, expected = integrity.partition("-")
    if algorithm != "sha512":
        raise IntegrityError(f"algorithme d'empreinte non supporté : {algorithm}")
    actual = base64.b64encode(hashlib.sha512(data).digest()).decode()
    if actual != expected:
        raise IntegrityError("empreinte sha512 différente de celle publiée par le registre")


def read_member(archive: bytes, member: str) -> bytes:
    # Lecture en mémoire : rien n'est extrait sur le disque (pas de risque de chemin malveillant).
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        extracted = tar.extractfile(f"package/{member}")
        if extracted is None:
            raise KeyError(member)
        return extracted.read()


def _download(url: str, integrity: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    verify_integrity(data, integrity)
    return data


def vendor() -> None:
    motion = _download(*MOTION)
    MOTION_DIR.mkdir(parents=True, exist_ok=True)
    (MOTION_DIR / "motion.js").write_bytes(read_member(motion, "dist/motion.js"))
    (MOTION_DIR / "motion-LICENSE.md").write_bytes(read_member(motion, "LICENSE.md"))

    phosphor = _download(*PHOSPHOR)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    (ICONS_DIR / "LICENSE").write_bytes(read_member(phosphor, "LICENSE"))
    for name in ICONS:
        (ICONS_DIR / f"{name}.svg").write_bytes(read_member(phosphor, f"assets/regular/{name}.svg"))


if __name__ == "__main__":
    vendor()
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS (tous les tests existants + les 6 nouveaux)

- [ ] **Step 5: Télécharger et vérifier les fichiers**

Run: `uv run python -m tools.vendor_assets && ls static/js/vendor app/static_src/icons | head -20 && head -c 120 static/js/vendor/motion.js`
Expected: `motion.js`, `motion-LICENSE.md`, 13 SVG + `LICENSE` ; `motion.js` commence par `!function(t,e){` et contient `.Motion={}`.

- [ ] **Step 6: Commit**

```bash
git add landing/tools landing/tests/test_vendor_assets.py landing/static/js/vendor landing/app/static_src/icons
git commit -m "feat(landing): vendor Motion and Phosphor icons with sha512 check"
```

---

### Task 2: Helper d'icônes pour les gabarits

**Files:**
- Create: `landing/app/icons.py`
- Modify: `landing/app/factory.py` (globals Jinja)
- Test: `landing/tests/test_icons.py`

**Interfaces:**
- Consumes: `tools.vendor_assets.ICONS_DIR`, fichiers SVG (Task 1).
- Produces: `icon(name: str, css_class: str = "size-6") -> markupsafe.Markup` ; nom inconnu → `ValueError`. Global Jinja `icon`.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_icons.py` :

```python
import pytest

from app.icons import icon
from tools.vendor_assets import ICONS


@pytest.mark.parametrize("name", ICONS)
def test_every_vendored_icon_renders_in_palette_color(name):
    svg = str(icon(name, "size-5 text-accent"))
    assert svg.startswith('<svg class="size-5 text-accent" aria-hidden="true" focusable="false" ')
    assert 'fill="currentColor"' in svg


def test_unknown_icon_fails_fast():
    with pytest.raises(ValueError, match="cloud-snow"):
        icon("cloud-snow")



def test_icon_is_available_in_templates(settings, repository):
    from fastapi.templating import Jinja2Templates

    from app.factory import create_app

    app = create_app(settings, repository)
    templates: Jinja2Templates = app.state.templates
    rendered = templates.env.from_string('{{ icon("map-pin", "size-4") }}').render()
    assert rendered.startswith('<svg class="size-4"')
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_icons.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app.icons'`

- [ ] **Step 3: Implémenter**

`landing/app/icons.py` :

```python
from functools import cache

from markupsafe import Markup

from tools.vendor_assets import ICONS, ICONS_DIR


@cache
def _svg(name: str) -> str:
    return (ICONS_DIR / f"{name}.svg").read_text().strip()


def icon(name: str, css_class: str = "size-6") -> Markup:
    if name not in ICONS:
        raise ValueError(f"icône inconnue : {name} (liste fermée dans tools/vendor_assets.py)")
    attributes = f'class="{css_class}" aria-hidden="true" focusable="false" '
    return Markup(_svg(name).replace("<svg ", f"<svg {attributes}", 1))
```

Dans `landing/app/factory.py`, ajouter l'import `from app.icons import icon`, ajouter `icon=icon,` dans `templates.env.globals.update(...)`, et juste après ce bloc :

```python
    app.state.templates = templates
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add landing/app/icons.py landing/app/factory.py landing/tests/test_icons.py
git commit -m "feat(landing): Phosphor icon helper for templates"
```

---

### Task 3: Modèle et géométrie de la démo

**Files:**
- Create: `landing/app/demo/__init__.py`, `landing/app/demo/scenario.py`, `landing/app/demo/route_geometry.py`
- Test: `landing/tests/test_demo.py`

**Interfaces:**
- Consumes: `tools.vendor_assets.ICONS`.
- Produces:
  - `Incident(kind: Literal["retrait", "ajout"], position: int, label: str, icon: str)`
  - `DemoScenario(debut: time, positions: tuple[tuple[float, float], ...], incident: Incident, sms: str, ajout_xy: tuple[float, float] | None = None)` ; `__post_init__` lève `ValueError` si : nombre de positions ≠ 5, retrait avec `position` hors `0..3`, ajout avec `position` hors `0..4`, ajout sans `ajout_xy`, retrait avec `ajout_xy`, `"{heure}"` absent du SMS, icône hors `ICONS`.
  - `DemoStop(key: str, heure: time, x: float, y: float)` ; clés `s0..s4` pour les arrêts de départ, `ajout` pour l'arrêt ajouté.
  - `STEP_MINUTES = 45`, `stops_before(s) -> tuple[DemoStop, ...]`, `stops_after(s) -> tuple[DemoStop, ...]`, `route_path(stops) -> str`, `format_heure(t: time) -> str`, `sms_text(s) -> str`.
  - `DemoMarker(key, x, y, heure_avant: str | None, heure_apres: str | None)`, `DemoView(markers, path_avant, path_apres, incident_key, incident_label, incident_icon, arrivee_key, sms)`, `demo_view(s) -> DemoView`.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_demo.py` :

```python
from datetime import time

import pytest

from app.demo.route_geometry import (
    demo_view,
    format_heure,
    route_path,
    sms_text,
    stops_after,
    stops_before,
)
from app.demo.scenario import DemoScenario, Incident

POSITIONS = ((30, 160), (90, 70), (160, 140), (230, 60), (290, 130))


def scenario(kind="retrait", position=2, ajout_xy=None, sms="Bonjour, votre passage est à {heure}.", icon="x-circle"):
    return DemoScenario(
        debut=time(8, 0),
        positions=POSITIONS,
        incident=Incident(kind=kind, position=position, label="Imprévu", icon=icon),
        sms=sms,
        ajout_xy=ajout_xy,
    )


def heures(stops):
    return [format_heure(stop.heure) for stop in stops]


def test_before_has_five_stops_every_45_minutes():
    assert heures(stops_before(scenario())) == ["8h00", "8h45", "9h30", "10h15", "11h00"]


def test_retrait_removes_the_stop_and_following_ones_move_earlier():
    after = stops_after(scenario(kind="retrait", position=2))
    assert [stop.key for stop in after] == ["s0", "s1", "s3", "s4"]
    assert heures(after) == ["8h00", "8h45", "9h30", "10h15"]


def test_ajout_inserts_a_stop_and_following_ones_move_later():
    after = stops_after(scenario(kind="ajout", position=2, ajout_xy=(140, 40)))
    assert [stop.key for stop in after] == ["s0", "s1", "ajout", "s2", "s3", "s4"]
    assert heures(after) == ["8h00", "8h45", "9h30", "10h15", "11h00", "11h45"]
    assert (after[2].x, after[2].y) == (140, 40)


def test_sms_announces_new_time_of_first_changed_stop():
    assert sms_text(scenario(kind="retrait", position=2)) == "Bonjour, votre passage est à 9h30."
    assert sms_text(scenario(kind="ajout", position=2, ajout_xy=(140, 40))) == "Bonjour, votre passage est à 10h15."


def test_retrait_of_first_stop_moves_next_client_to_start_time():
    assert sms_text(scenario(kind="retrait", position=0)) == "Bonjour, votre passage est à 8h00."


def test_format_heure_has_no_leading_zero():
    assert format_heure(time(7, 0)) == "7h00"
    assert format_heure(time(10, 5)) == "10h05"


def test_route_path_goes_through_first_and_last_stop():
    stops = stops_before(scenario())
    path = route_path(stops)
    assert path.startswith("M30,160 ")
    assert path.endswith(" 290,130")
    assert path.count("C") == len(stops) - 1


def test_demo_view_keeps_removed_stop_hidden_in_final_state():
    view = demo_view(scenario(kind="retrait", position=2))
    removed = next(marker for marker in view.markers if marker.key == "s2")
    assert (removed.heure_avant, removed.heure_apres) == ("9h30", None)
    moved = next(marker for marker in view.markers if marker.key == "s3")
    assert (moved.heure_avant, moved.heure_apres) == ("10h15", "9h30")
    assert view.incident_key == "s2"
    assert view.arrivee_key == "s4"
    assert view.path_apres == route_path(stops_after(scenario(kind="retrait", position=2)))


def test_demo_view_lists_added_stop_without_before_time():
    view = demo_view(scenario(kind="ajout", position=2, ajout_xy=(140, 40)))
    added = next(marker for marker in view.markers if marker.key == "ajout")
    assert (added.heure_avant, added.heure_apres) == (None, "9h30")
    assert view.incident_key == "ajout"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "retrait", "position": 4},
        {"kind": "retrait", "position": -1},
        {"kind": "ajout", "position": 5, "ajout_xy": (1, 1)},
        {"kind": "ajout", "position": 1},
        {"kind": "retrait", "position": 1, "ajout_xy": (1, 1)},
        {"sms": "Bonjour, sans heure."},
        {"icon": "cloud-snow"},
    ],
)
def test_invalid_scenario_fails_fast(kwargs):
    with pytest.raises(ValueError):
        scenario(**kwargs)


def test_scenario_needs_exactly_five_positions():
    with pytest.raises(ValueError):
        DemoScenario(
            debut=time(8, 0),
            positions=POSITIONS[:4],
            incident=Incident(kind="retrait", position=1, label="Imprévu", icon="x-circle"),
            sms="{heure}",
        )
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_demo.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app.demo'`

- [ ] **Step 3: Implémenter**

`landing/app/demo/__init__.py` : fichier vide.

`landing/app/demo/scenario.py` :

```python
from dataclasses import dataclass
from datetime import time
from typing import Literal

from tools.vendor_assets import ICONS

STOP_COUNT = 5


@dataclass(frozen=True)
class Incident:
    kind: Literal["retrait", "ajout"]
    position: int
    label: str
    icon: str


@dataclass(frozen=True)
class DemoStop:
    key: str
    heure: time
    x: float
    y: float


@dataclass(frozen=True)
class DemoScenario:
    debut: time
    positions: tuple[tuple[float, float], ...]
    incident: Incident
    sms: str
    ajout_xy: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if len(self.positions) != STOP_COUNT:
            raise ValueError(f"une démo a exactement {STOP_COUNT} arrêts de départ")
        # Retrait du dernier arrêt ou ajout après lui : aucun client ne changerait d'heure, pas de SMS possible.
        last_position = STOP_COUNT - 2 if self.incident.kind == "retrait" else STOP_COUNT - 1
        if not 0 <= self.incident.position <= last_position:
            raise ValueError(f"position d'imprévu invalide : {self.incident.position}")
        if (self.incident.kind == "ajout") != (self.ajout_xy is not None):
            raise ValueError("ajout_xy est requis pour un ajout et interdit pour un retrait")
        if "{heure}" not in self.sms:
            raise ValueError("le SMS doit contenir {heure}")
        if self.incident.icon not in ICONS:
            raise ValueError(f"icône inconnue : {self.incident.icon}")
```

`landing/app/demo/route_geometry.py` :

```python
from dataclasses import dataclass
from datetime import time

from app.demo.scenario import DemoScenario, DemoStop

STEP_MINUTES = 45


def _heure_at(debut: time, index: int) -> time:
    minutes = debut.hour * 60 + debut.minute + index * STEP_MINUTES
    return time(minutes // 60, minutes % 60)


def stops_before(scenario: DemoScenario) -> tuple[DemoStop, ...]:
    return tuple(
        DemoStop(f"s{index}", _heure_at(scenario.debut, index), x, y)
        for index, (x, y) in enumerate(scenario.positions)
    )


def stops_after(scenario: DemoScenario) -> tuple[DemoStop, ...]:
    keyed = [(f"s{index}", xy) for index, xy in enumerate(scenario.positions)]
    if scenario.incident.kind == "retrait":
        del keyed[scenario.incident.position]
    else:
        keyed.insert(scenario.incident.position, ("ajout", scenario.ajout_xy))
    return tuple(
        DemoStop(key, _heure_at(scenario.debut, index), x, y) for index, (key, (x, y)) in enumerate(keyed)
    )


def format_heure(heure: time) -> str:
    return f"{heure.hour}h{heure.minute:02d}"


def route_path(stops: tuple[DemoStop, ...]) -> str:
    # Catmull-Rom converti en courbes de Bézier : une route souple qui passe par chaque arrêt.
    points = [(stop.x, stop.y) for stop in stops]
    commands = [f"M{points[0][0]:g},{points[0][1]:g}"]
    for index in range(len(points) - 1):
        p0 = points[index - 1] if index > 0 else points[index]
        p1, p2 = points[index], points[index + 1]
        p3 = points[index + 2] if index + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        commands.append(f"C{c1[0]:g},{c1[1]:g} {c2[0]:g},{c2[1]:g} {p2[0]:g},{p2[1]:g}")
    return " ".join(commands)


def sms_text(scenario: DemoScenario) -> str:
    before = {stop.key: stop.heure for stop in stops_before(scenario)}
    changed = next(stop for stop in stops_after(scenario) if stop.key in before and before[stop.key] != stop.heure)
    return scenario.sms.format(heure=format_heure(changed.heure))


@dataclass(frozen=True)
class DemoMarker:
    key: str
    x: float
    y: float
    heure_avant: str | None
    heure_apres: str | None


@dataclass(frozen=True)
class DemoView:
    markers: tuple[DemoMarker, ...]
    path_avant: str
    path_apres: str
    incident_key: str
    incident_label: str
    incident_icon: str
    arrivee_key: str
    sms: str


def demo_view(scenario: DemoScenario) -> DemoView:
    before = {stop.key: stop for stop in stops_before(scenario)}
    after_stops = stops_after(scenario)
    after = {stop.key: stop for stop in after_stops}
    keys = list(before) + [key for key in after if key not in before]
    markers = tuple(
        DemoMarker(
            key=key,
            x=(after.get(key) or before[key]).x,
            y=(after.get(key) or before[key]).y,
            heure_avant=format_heure(before[key].heure) if key in before else None,
            heure_apres=format_heure(after[key].heure) if key in after else None,
        )
        for key in keys
    )
    incident = scenario.incident
    return DemoView(
        markers=markers,
        path_avant=route_path(tuple(before.values())),
        path_apres=route_path(after_stops),
        incident_key=f"s{incident.position}" if incident.kind == "retrait" else "ajout",
        incident_label=incident.label,
        incident_icon=incident.icon,
        arrivee_key=after_stops[-1].key,
        sms=sms_text(scenario),
    )
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add landing/app/demo landing/tests/test_demo.py
git commit -m "feat(landing): demo scenario model and route geometry"
```

---

### Task 4: Contenus (scénario par métier, icônes, économie animable)

**Files:**
- Modify: `landing/app/content/models.py`, `landing/app/content/commun.py`, `landing/app/content/generique.py`, `landing/app/content/laveur_vitres.py`, `landing/app/content/infirmier.py`, `landing/app/content/services_domicile.py`
- Test: `landing/tests/test_offer_and_content.py` (ajouts)

**Interfaces:**
- Consumes: `DemoScenario`, `Incident`, `sms_text` (T3), `ICONS` (T1).
- Produces: `Pain(probleme, solution, icone)`, `Variant(..., douleurs, demo: DemoScenario)`, `commun.FAISABILITE` / `commun.MORALE` en triplets `(titre, texte, icone)`, `commun.ECONOMIE_AVANT: str`, `commun.ECONOMIE_MONTANT: int`, `commun.ECONOMIE_APRES: str` (remplacent `commun.ECONOMIE`), `commun.REJOUER: str`.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `landing/tests/test_offer_and_content.py` (imports en tête du fichier : `from app.demo.route_geometry import sms_text` et `from tools.vendor_assets import ICONS`) :

```python
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
    assert commun.ECONOMIE_MONTANT == offer.economie_annuelle_ht()
    assert commun.ECONOMIE_AVANT + str(commun.ECONOMIE_MONTANT) + commun.ECONOMIE_APRES == (
        "-10 € HT/mois à vie, soit 120 € HT économisés chaque année."
    )


def test_demo_copy_follows_copy_rules():
    for variant in VARIANTS.values():
        for text in (variant.demo.incident.label, sms_text(variant.demo)):
            assert "—" not in text
            assert not TUTOIEMENT.search(text)
    nurse = (VARIANTS["infirmier"].demo.incident.label + sms_text(VARIANTS["infirmier"].demo)).lower()
    assert not [word for word in HEALTH_WORDS if word in nurse]
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_offer_and_content.py -q`
Expected: FAIL `AttributeError: 'Variant' object has no attribute 'demo'` (et `ECONOMIE_MONTANT` absent)

- [ ] **Step 3: Mettre à jour les modèles**

`landing/app/content/models.py` (remplacer tout le fichier) :

```python
from dataclasses import dataclass

from app.demo.scenario import DemoScenario


@dataclass(frozen=True)
class Pain:
    probleme: str
    solution: str
    icone: str


@dataclass(frozen=True)
class Variant:
    slug: str
    path: str
    metier_prefill: str | None
    h1: str
    sous_titre: str
    douleurs: tuple[Pain, Pain, Pain]
    demo: DemoScenario
```

- [ ] **Step 4: Mettre à jour `commun.py`**

Remplacer les blocs `FAISABILITE`, `MORALE` et la ligne `ECONOMIE = ...` par :

```python
FAISABILITE = (
    ("Prise en main en 5 minutes.", "On importe vos clients avec vous, au téléphone si besoin.", "clock-countdown"),
    ("Votre tournée sur papier.", "Un PDF clair, imprimable chaque matin.", "printer"),
    ("Vous gardez la main.", "Bouclé propose, vous validez ou vous modifiez. Toujours.", "hand-heart"),
)
```

```python
MORALE = (
    ("Hébergées en France.", "Jamais revendues, jamais partagées.", "shield-check"),
    ("Vos clients respectés.", "Prévenus avant, jamais surpris par un retard.", "chat-text"),
    ("Du temps rendu.", "Moins de trajets et de coups de fil, plus de soirées pour vous et vos proches.", "clock-countdown"),
)
```

```python
ECONOMIE_AVANT = f"-{PRIX_HT - PRIX_EARLY_ACCESS_HT} € HT/mois à vie, soit "
ECONOMIE_MONTANT = economie_annuelle_ht()
ECONOMIE_APRES = " € HT économisés chaque année."
```

Et ajouter sous `CTA = ...` :

```python
REJOUER = "Rejouer la démo"
```

- [ ] **Step 5: Mettre à jour les 4 variantes**

Dans chaque fichier, ajouter les imports :

```python
from datetime import time

from app.demo.scenario import DemoScenario, Incident
```

Ajouter un 3e argument (icône) à chaque `Pain(...)`, dans l'ordre des douleurs :
- `generique.py` : `"calendar-check"`, `"map-pin"`, `"printer"`
- `laveur_vitres.py` : `"cloud-rain"`, `"calendar-check"`, `"chat-text"`
- `infirmier.py` : `"clock-countdown"`, `"user-minus"`, `"map-pin"`
- `services_domicile.py` : `"plus-circle"`, `"calendar-check"`, `"map-pin"`

Exemple pour la première douleur générique :

```python
        Pain(
            "Un client annule, un autre ajoute un passage.",
            "Votre tournée se réorganise en un geste. Les clients concernés reçoivent leur nouvel horaire par SMS.",
            "calendar-check",
        ),
```

Puis ajouter l'argument `demo=` à chaque `Variant(...)`, après `douleurs=(...)` :

`generique.py` :

```python
    demo=DemoScenario(
        debut=time(8, 0),
        positions=((30, 160), (90, 70), (160, 140), (230, 60), (290, 130)),
        incident=Incident(kind="ajout", position=2, label="Un client ajoute un passage", icon="plus-circle"),
        ajout_xy=(140, 40),
        sms="Bonjour, votre passage est décalé à {heure}. Bouclé.tech",
    ),
```

`laveur_vitres.py` :

```python
    demo=DemoScenario(
        debut=time(7, 0),
        positions=((30, 150), (85, 60), (150, 120), (215, 50), (285, 110)),
        incident=Incident(kind="retrait", position=0, label="Annulation à 7h", icon="x-circle"),
        sms="Bonjour, nous pouvons passer plus tôt : {heure}. Bouclé.tech",
    ),
```

`infirmier.py` :

```python
    demo=DemoScenario(
        debut=time(7, 30),
        positions=((30, 60), (90, 140), (155, 70), (220, 150), (290, 80)),
        incident=Incident(kind="retrait", position=2, label="Patient absent", icon="user-minus"),
        sms="Bonjour, mon passage chez vous est avancé à {heure}. Bouclé.tech",
    ),
```

`services_domicile.py` :

```python
    demo=DemoScenario(
        debut=time(13, 30),
        positions=((30, 120), (100, 50), (170, 130), (240, 60), (295, 140)),
        incident=Incident(kind="ajout", position=1, label="Demande urgente", icon="lightning"),
        ajout_xy=(60, 40),
        sms="Bonjour, votre passage est décalé à {heure}. Bouclé.tech",
    ),
```

- [ ] **Step 6: Adapter le gabarit existant aux triplets et à l'économie découpée**

Dans `landing/app/templates/landing.html`, remplacer `{% for item_title, item_text in items %}` par `{% for item_title, item_text, item_icon in items %}` et `{{ commun.ECONOMIE }}` par `{{ commun.ECONOMIE_AVANT }}{{ commun.ECONOMIE_MONTANT }}{{ commun.ECONOMIE_APRES }}` (la refonte complète du gabarit vient en Task 5 ; ici on garde la suite verte).

- [ ] **Step 7: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add landing/app/content landing/app/templates/landing.html landing/tests/test_offer_and_content.py
git commit -m "feat(landing): per-trade demo scenarios and content icons"
```

---

### Task 5: Gabarits (démo, fil de la route, prix, compteur, merci)

**Files:**
- Create: `landing/app/templates/_demo.html`
- Modify: `landing/app/templates/landing.html` (remplacé entièrement), `landing/app/templates/merci.html`, `landing/app/routes.py` (contexte), `landing/app/factory.py` (global `demo_view`)
- Test: `landing/tests/test_pages.py` (ajouts)

**Interfaces:**
- Consumes: `demo_view(scenario) -> DemoView` (T3), `variant.demo`, `Pain.icone`, triplets `FAISABILITE`/`MORALE`, `ECONOMIE_*`, `REJOUER` (T4), `icon` (T2), `offer.PLACES_EARLY_ACCESS`.
- Produces (contrat DOM pour Task 6) :
  - démo : `figure[data-demo]` contenant `path[data-route-before]`, `path[data-route-after]`, `g[data-marker][data-heure-avant][data-heure-apres]` avec un `text[data-heure]`, `[data-incident]`, `[data-sms]`, `button[data-demo-replay]`.
  - fil : `[data-route-thread] path` ; arrêts `span[data-route-stop].route-stop.is-reached`.
  - révélation : conteneurs `[data-reveal-group]` (enfants animés).
  - prix : `[data-offer]` contenant `[data-strike-line]`, `[data-price-early]`, `[data-count-to]`, pastilles `[data-place-dot]` (prises : `data-place-taken`).
  - scripts : `motion.js`, `demo.js`, `route-scroll.js`, `lead-form.js` en `defer`, dans cet ordre.

- [ ] **Step 1: Écrire les tests qui échouent**

Ajouter à `landing/tests/test_pages.py` (import en tête : `from app.demo.route_geometry import demo_view` et `from app.offer import PLACES_EARLY_ACCESS`) :

```python
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


def test_route_thread_and_reached_stops_are_visible_without_js(client):
    text = page(client, "/")
    assert "data-route-thread" in text
    assert text.count('data-route-stop class="route-stop is-reached"') == 4


def test_each_pain_card_shows_its_icon(client):
    text = page(client, "/infirmier")
    assert text.count('<svg class="size-7 text-principale"') >= 3


def test_yearly_saving_is_final_without_js(client):
    assert 'data-count-to="120">120</span>' in page(client, "/")


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
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_pages.py -q`
Expected: FAIL (8 nouveaux tests : `data-demo` absent, scripts absents, etc.)

- [ ] **Step 3: Exposer `demo_view` et le nombre de places aux gabarits**

Dans `landing/app/factory.py`, ajouter l'import `from app.demo.route_geometry import demo_view` et l'entrée `demo_view=demo_view,` dans `templates.env.globals.update(...)`.

Dans `landing/app/routes.py`, importer `PLACES_EARLY_ACCESS` (`from app.offer import PLACES_EARLY_ACCESS, est_en_liste_attente, places_restantes`) et ajouter au contexte de `variant_page` :

```python
                    "places_total": PLACES_EARLY_ACCESS,
```

- [ ] **Step 4: Créer `_demo.html`**

`landing/app/templates/_demo.html` :

```html
{% set demo = demo_view(variant.demo) %}
<figure data-demo class="mt-10 rounded-3xl bg-principale/5 p-4 ring-1 ring-texte/10 sm:p-6">
  <figcaption class="flex items-center justify-between gap-3">
    <p data-incident class="inline-flex items-center gap-2 rounded-full bg-fond px-3 py-1.5 text-sm font-bold ring-1 ring-texte/15">
      {{ icon(demo.incident_icon, "size-5 text-accent") }}{{ demo.incident_label }}
    </p>
    <button type="button" data-demo-replay class="rounded-full p-2 text-principale ring-1 ring-texte/15" aria-label="{{ commun.REJOUER }}">
      {{ icon("arrow-counter-clockwise", "size-5") }}
    </button>
  </figcaption>
  <svg viewBox="0 0 320 200" class="mt-3 w-full" role="img" aria-label="{{ demo.incident_label }} : la tournée se recalcule et les clients sont prévenus par SMS.">
    <path d="M0 40 H320 M0 100 H320 M0 160 H320 M60 0 V200 M140 0 V200 M220 0 V200" fill="none" stroke="currentColor" stroke-width="1" class="text-principale/15"/>
    <path data-route-before d="{{ demo.path_avant }}" pathLength="1" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" class="text-principale" opacity="0"/>
    <path data-route-after d="{{ demo.path_apres }}" pathLength="1" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" class="text-principale"/>
    {% for marker in demo.markers %}
    <g data-marker="{{ marker.key }}" data-heure-avant="{{ marker.heure_avant or '' }}" data-heure-apres="{{ marker.heure_apres or '' }}"{% if marker.heure_apres is none %} opacity="0"{% endif %}>
      {% if marker.key == demo.arrivee_key %}
      <circle cx="{{ marker.x }}" cy="{{ marker.y }}" r="12" fill="none" stroke="currentColor" stroke-width="2" class="text-accent"/>
      <circle cx="{{ marker.x }}" cy="{{ marker.y }}" r="7" fill="currentColor" class="text-accent"/>
      {% else %}
      <circle cx="{{ marker.x }}" cy="{{ marker.y }}" r="7" fill="var(--color-fond)" stroke="currentColor" stroke-width="3" class="text-principale"/>
      {% endif %}
      <text data-heure x="{{ marker.x }}" y="{{ marker.y - 15 }}" text-anchor="middle" class="fill-texte text-[11px] font-bold">{{ marker.heure_apres or marker.heure_avant }}</text>
    </g>
    {% endfor %}
  </svg>
  <p data-sms class="mx-auto mt-3 flex max-w-sm items-start gap-2 rounded-2xl bg-fond p-3 text-sm ring-1 ring-texte/10">
    {{ icon("chat-text", "size-5 shrink-0 text-principale") }}<span>{{ demo.sms }}</span>
  </p>
</figure>
```

- [ ] **Step 5: Remplacer `landing.html`**

`landing/app/templates/landing.html` (remplacer tout le fichier) :

```html
{% extends "base.html" %}
{% block description %}{{ variant.sous_titre }}{% endblock %}
{% block main %}
<div class="relative">
  <div data-route-thread class="pointer-events-none absolute inset-y-0 left-1 w-3 sm:left-4" aria-hidden="true">
    <svg class="h-full w-full" viewBox="0 0 12 1000" preserveAspectRatio="none">
      <path d="M6 0 C12 125 0 250 6 375 C12 500 0 625 6 750 C12 875 0 950 6 1000" pathLength="1" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" vector-effect="non-scaling-stroke" class="text-principale/40"/>
    </svg>
  </div>

  <section class="mx-auto max-w-5xl px-4 pt-6 pb-16">
    <h1 class="font-douleur text-4xl leading-tight font-semibold sm:text-6xl">{{ variant.h1 }}</h1>
    <p class="mt-5 max-w-2xl text-lg sm:text-xl">{{ variant.sous_titre }}</p>
    {% include "_demo.html" %}
    <a href="#formulaire" class="mt-8 inline-block rounded-2xl bg-accent px-7 py-4 text-lg font-extrabold text-texte">{{ commun.CTA }}</a>
    <p class="mt-3 font-bold">{{ commun.SOUS_CTA }}</p>
  </section>

  <section class="bg-principale/5 py-16">
    <div class="mx-auto max-w-5xl px-4">
      <h2 class="text-3xl font-bold text-principale"><span data-route-stop class="route-stop is-reached" aria-hidden="true"></span>{{ commun.UTILITE_TITRE }}</h2>
      <ul data-reveal-group class="mt-8 grid gap-5 sm:grid-cols-3">
        {% for pain in variant.douleurs %}
        <li class="rounded-2xl bg-fond p-6 ring-1 ring-texte/10">
          {{ icon(pain.icone, "size-7 text-principale") }}
          <p class="mt-4 text-lg font-bold">{{ pain.probleme }}</p>
          <p class="mt-3">{{ pain.solution }}</p>
        </li>
        {% endfor %}
      </ul>
    </div>
  </section>

  {% for title, items in [(commun.FAISABILITE_TITRE, commun.FAISABILITE), (commun.MORALE_TITRE, commun.MORALE)] %}
  <section class="mx-auto max-w-5xl px-4 py-16">
    <h2 class="text-3xl font-bold text-principale"><span data-route-stop class="route-stop is-reached" aria-hidden="true"></span>{{ title }}</h2>
    <ul data-reveal-group class="mt-8 grid gap-6 sm:grid-cols-3">
      {% for item_title, item_text, item_icon in items %}
      <li>
        {{ icon(item_icon, "size-7 text-principale") }}
        <p class="mt-3 text-lg font-bold">{{ item_title }}</p>
        <p class="mt-2">{{ item_text }}</p>
      </li>
      {% endfor %}
    </ul>
  </section>
  {% endfor %}

  <section class="bg-principale/5 py-16">
    <div data-offer class="mx-auto max-w-5xl px-4">
      <h2 class="text-3xl font-bold text-principale"><span data-route-stop class="route-stop is-reached" aria-hidden="true"></span>{{ commun.OPPORTUNITE_TITRE }}</h2>
      <p class="mt-6 flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <s class="relative text-xl text-texte/60 [text-decoration:none]">{{ commun.PRIX_NORMAL }}<span data-strike-line class="absolute inset-x-0 top-1/2 h-0.5 origin-left bg-texte/60" aria-hidden="true"></span></s>
        <span data-price-early class="inline-block text-4xl font-extrabold text-accent">{{ commun.PRIX_EARLY }}</span>
      </p>
      <p class="mt-3 text-lg font-bold">{{ commun.ECONOMIE_AVANT }}<span data-count-to="{{ commun.ECONOMIE_MONTANT }}">{{ commun.ECONOMIE_MONTANT }}</span>{{ commun.ECONOMIE_APRES }}</p>
      <div class="mt-6 flex flex-wrap gap-2" aria-hidden="true">
        {% for index in range(places_total) %}
        <span data-place-dot{% if index < places_total - places %} data-place-taken{% endif %} class="size-4 rounded-full {{ 'bg-accent' if index < places_total - places else 'ring-2 ring-accent' }}"></span>
        {% endfor %}
      </div>
      <p class="mt-3 text-xl font-bold text-accent">{{ commun.compteur(places) }}</p>
      <p class="mt-3 max-w-2xl">{{ commun.ATTENTE }}</p>
    </div>
  </section>

  <section id="formulaire" class="mx-auto max-w-xl px-4 py-16">
    <h2 class="text-3xl font-bold text-principale">{{ commun.FORMULAIRE_TITRE }}</h2>
    <p class="mt-2">{{ commun.FORMULAIRE_INTRO }}</p>
    <form data-lead-form data-network-error="{{ commun.INDISPONIBLE.format(contact_email=contact_email) }}" class="mt-8 space-y-6" novalidate>
      <input type="hidden" name="variante" value="{{ variant.slug }}">
      <input type="hidden" name="utm_source" value="{{ utm_source }}">
      <input type="hidden" name="utm_campaign" value="{{ utm_campaign }}">

      <label class="block">
        <span class="font-bold">{{ commun.LABELS.metier }}</span>
        <select name="metier" required class="mt-2 block w-full rounded-xl bg-fond p-3 text-lg ring-1 ring-texte/30">
          <option value="" disabled{% if not variant.metier_prefill %} selected{% endif %}>Choisissez</option>
          {% for value, label in commun.METIERS %}
          <option value="{{ value }}"{% if value == variant.metier_prefill %} selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
        <span data-error-for="metier" class="mt-1 block font-bold"></span>
      </label>

      {% for field, options in [("taille", commun.TAILLES), ("douleur", commun.DOULEURS)] %}
      <fieldset>
        <legend class="font-bold">{{ commun.LABELS[field] }}</legend>
        <div class="mt-2 grid gap-2">
          {% for value, label in options %}
          <label class="flex items-center gap-3 rounded-xl p-3 text-lg ring-1 ring-texte/20">
            <input type="radio" name="{{ field }}" value="{{ value }}" required class="size-5 accent-principale"> {{ label }}
          </label>
          {% endfor %}
        </div>
        <span data-error-for="{{ field }}" class="mt-1 block font-bold"></span>
      </fieldset>
      {% endfor %}

      {% for field, type, autocomplete in [("email", "email", "email"), ("phone", "tel", "tel")] %}
      <label class="block">
        <span class="font-bold">{{ commun.LABELS[field] }}</span>
        <input type="{{ type }}" name="{{ field }}" autocomplete="{{ autocomplete }}" required class="mt-2 block w-full rounded-xl bg-fond p-3 text-lg ring-1 ring-texte/30">
        <span data-error-for="{{ field }}" class="mt-1 block font-bold"></span>
      </label>
      {% endfor %}

      <label class="flex items-start gap-3">
        <input type="checkbox" name="accepte_appel" class="mt-1 size-5 shrink-0 accent-principale">
        <span>{{ commun.ACCEPTE_APPEL }}</span>
      </label>
      <div>
        <label class="flex items-start gap-3">
          <input type="checkbox" name="consentement_rgpd" required class="mt-1 size-5 shrink-0 accent-principale">
          <span>{{ commun.CONSENTEMENT }} <a class="underline" href="/confidentialite">Politique de confidentialité</a></span>
        </label>
        <span data-error-for="consentement_rgpd" class="mt-1 block font-bold"></span>
      </div>

      <div class="honeypot" aria-hidden="true">
        <label>Site web <input type="text" name="website" tabindex="-1" autocomplete="off"></label>
      </div>

      <button type="submit" class="cta-arrivee w-full rounded-2xl bg-accent px-7 py-4 text-lg font-extrabold text-texte disabled:opacity-60">{{ commun.CTA }}</button>
      <p data-form-status role="status" class="font-bold"></p>
    </form>
  </section>
</div>
{% endblock %}
{% block scripts %}
<script src="/static/js/vendor/motion.js" defer></script>
<script src="/static/js/demo.js" defer></script>
<script src="/static/js/route-scroll.js" defer></script>
<script src="/static/js/lead-form.js" defer></script>
{% endblock %}
```

- [ ] **Step 6: Page merci : la route se boucle**

Dans `landing/app/templates/merci.html`, insérer juste après `<section class="mx-auto max-w-2xl px-4 py-20">` :

```html
  <span class="logo mx-auto block size-28" aria-hidden="true">{{ logo_svg | safe }}</span>
```

et ajouter `mt-8 text-center` aux classes du `<h1>` (devient `class="mt-8 text-center font-douleur text-5xl font-semibold"`). L'animation de tracé `.logo path` existe déjà dans `input.css`.

- [ ] **Step 7: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS (dont `test_templates_have_no_inline_script` et `test_copy_uses_vouvoiement_and_no_em_dash` qui scannent `_demo.html`)

- [ ] **Step 8: Commit**

```bash
git add landing/app/templates landing/app/routes.py landing/app/factory.py landing/tests/test_pages.py
git commit -m "feat(landing): live demo, route thread, price and counter markup"
```

---

### Task 6: Animations (JS + CSS), vérification visuelle, mise à jour de la spec

**Files:**
- Create: `landing/static/js/demo.js`, `landing/static/js/route-scroll.js`
- Modify: `landing/app/static_src/input.css`, `docs/superpowers/specs/2026-10-14-landing-animations-design.md`

**Interfaces:**
- Consumes: contrat DOM de Task 5, `window.Motion` (`animate`, `inView`, `scroll`, `stagger`) chargé par `vendor/motion.js`.
- Produces: comportement visuel. Pas de test automatisé JS (pas de npm ; aucune logique : données calculées en Python).

- [ ] **Step 1: Styles des arrêts et du halo**

Ajouter à la fin de `landing/app/static_src/input.css` :

```css
.route-stop {
  display: inline-block;
  width: 0.875rem;
  height: 0.875rem;
  margin-right: 0.75rem;
  vertical-align: middle;
  border: 3px solid var(--color-principale);
  border-radius: 9999px;
  background: var(--color-fond);
  transition: background-color 0.4s ease-out;
}

.route-stop.is-reached {
  background: var(--color-principale);
}

/* Le CTA du formulaire est l'arrivée de la route : même halo qui respire que le logo. */
@keyframes halo-arrivee {
  0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--color-accent) 45%, transparent); }
  50% { box-shadow: 0 0 0 12px color-mix(in srgb, var(--color-accent) 0%, transparent); }
}

.cta-arrivee {
  animation: halo-arrivee 2.4s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .cta-arrivee { animation: none; }
  .route-stop { transition: none; }
}
```

- [ ] **Step 2: Script de la démo**

`landing/static/js/demo.js` :

```js
const Motion = window.Motion;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function setupDemo(figure) {
  const { animate, inView, stagger } = Motion;
  const before = figure.querySelector("[data-route-before]");
  const after = figure.querySelector("[data-route-after]");
  const markers = [...figure.querySelectorAll("[data-marker]")];
  const incident = figure.querySelector("[data-incident]");
  const sms = figure.querySelector("[data-sms]");
  const replay = figure.querySelector("[data-demo-replay]");
  const removed = markers.filter((marker) => !marker.dataset.heureApres);
  const added = markers.filter((marker) => !marker.dataset.heureAvant);
  const initial = markers.filter((marker) => marker.dataset.heureAvant);
  let running = false;
  let looping = false;
  let visible = false;

  function setTimes(key) {
    for (const marker of markers) {
      const value = marker.dataset[key];
      if (value) marker.querySelector("[data-heure]").textContent = value;
    }
  }

  function resetToStart() {
    before.style.strokeDasharray = "1";
    before.style.strokeDashoffset = "1";
    before.style.opacity = "1";
    after.style.strokeDasharray = "1";
    after.style.strokeDashoffset = "1";
    for (const marker of markers) marker.style.opacity = "0";
    setTimes("heureAvant");
    incident.style.opacity = "0";
    sms.style.opacity = "0";
  }

  async function play() {
    if (running) return;
    running = true;
    resetToStart();
    animate(before, { strokeDashoffset: [1, 0] }, { duration: 1.2, ease: "easeOut" });
    await animate(initial, { opacity: [0, 1] }, { delay: stagger(0.2), duration: 0.3 });
    await animate(incident, { opacity: [0, 1], y: [-8, 0] }, { delay: 0.3, duration: 0.4 });
    await Promise.all([
      animate(removed, { opacity: 0 }, { duration: 0.5 }),
      animate(before, { opacity: 0.25 }, { duration: 0.5 }),
    ]);
    await Promise.all([
      animate(after, { strokeDashoffset: [1, 0] }, { duration: 1, ease: "easeInOut" }),
      animate(added, { opacity: [0, 1] }, { delay: 0.3, duration: 0.4 }),
    ]);
    setTimes("heureApres");
    await animate(before, { opacity: 0 }, { duration: 0.3 });
    await animate(sms, { opacity: [0, 1], y: [16, 0] }, { duration: 0.5 });
    running = false;
  }

  async function loop() {
    if (looping) return;
    looping = true;
    while (visible) {
      await play();
      await wait(4000);
    }
    looping = false;
  }

  inView(figure, () => {
    visible = true;
    loop();
    return () => {
      visible = false;
    };
  });
  replay.addEventListener("click", play);
}

if (Motion && !reduceMotion) {
  document.querySelectorAll("[data-demo]").forEach(setupDemo);
}
```

- [ ] **Step 3: Script du fil de la route et des petits moments**

`landing/static/js/route-scroll.js` :

```js
const Motion = window.Motion;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function setupThread() {
  const { animate, scroll } = Motion;
  const thread = document.querySelector("[data-route-thread] path");
  const main = document.querySelector("main");
  if (!thread || !main) return;
  thread.style.strokeDasharray = "1";
  thread.style.strokeDashoffset = "1";
  scroll(animate(thread, { strokeDashoffset: [1, 0] }, { ease: "linear" }), {
    target: main,
    offset: ["start start", "end end"],
  });
}

function setupStops() {
  for (const stop of document.querySelectorAll("[data-route-stop]")) {
    stop.classList.remove("is-reached");
    Motion.inView(stop, () => stop.classList.add("is-reached"), { amount: 1 });
  }
}

function setupReveals() {
  const { animate, inView, stagger } = Motion;
  for (const group of document.querySelectorAll("[data-reveal-group]")) {
    const items = [...group.children];
    for (const item of items) item.style.opacity = "0";
    inView(group, () => {
      animate(items, { opacity: [0, 1], y: [24, 0] }, { delay: stagger(0.12), duration: 0.5 });
    }, { amount: 0.3 });
  }
}

function setupOffer() {
  const { animate, inView, stagger } = Motion;
  const offer = document.querySelector("[data-offer]");
  if (!offer) return;
  const strike = offer.querySelector("[data-strike-line]");
  const early = offer.querySelector("[data-price-early]");
  const amount = offer.querySelector("[data-count-to]");
  const dots = [...offer.querySelectorAll("[data-place-dot]")];
  const target = Number(amount.dataset.countTo);
  strike.style.transform = "scaleX(0)";
  early.style.opacity = "0";
  amount.textContent = "0";
  for (const dot of dots) dot.style.transform = "scale(0)";

  inView(offer, async () => {
    await animate(strike, { scaleX: [0, 1] }, { duration: 0.5, ease: "easeOut" });
    animate(early, { opacity: [0, 1], scale: [0.9, 1] }, { duration: 0.4 });
    animate(0, target, {
      duration: 1.2,
      ease: "easeOut",
      onUpdate: (value) => {
        amount.textContent = String(Math.round(value));
      },
    });
    animate(dots, { scale: [0, 1] }, { delay: stagger(0.05), duration: 0.3 });
  }, { amount: 0.5 });
}

if (Motion && !reduceMotion) {
  setupThread();
  setupStops();
  setupReveals();
  setupOffer();
}
```

- [ ] **Step 4: Compiler le CSS et relancer les tests**

Run :

```bash
TAILWINDCSS_VERSION=v4.1.11 uv run tailwindcss -i app/static_src/input.css -o static/css/app.css --minify
uv run pytest -q
```

Expected : CSS compilé ; tests PASS. Puis `grep -c -- "--color-red-500" static/css/app.css` → `0`.

- [ ] **Step 5: Vérification visuelle (serveur réel + captures headless)**

Lancer `uv run uvicorn app.main:app --port 8000` (cwd `landing/`, `secret.toml` présent) puis, avec Chrome headless (`--headless=new --hide-scrollbars --screenshot`), capturer `/` et `/laveur-vitres` :

- [ ] desktop 1280 px avec `--virtual-time-budget=500`, `2500`, `6000` : route en cours de tracé → imprévu affiché → nouvelle route + SMS ; aucune console d'erreur (`--enable-logging=stderr --v=0`, chercher `Uncaught`).
- [ ] mobile : Firefox headless `--window-size=375,2400` et `--window-size=320,2400` : heures et SMS lisibles, pas de débordement horizontal (Review Focus 1).
- [ ] Chrome `--force-prefers-reduced-motion` : état final immédiat, aucune pastille ni carte invisible (Review Focus 3).
- [ ] Chrome `--blink-settings=scriptEnabled=false` : état final complet (Review Focus 2).
- [ ] `/merci` : grand logo, « C'est bouclé. » centré.
- [ ] Poids : `gzip -c static/js/vendor/motion.js static/js/demo.js static/js/route-scroll.js static/js/lead-form.js | wc -c` ≤ 61440 octets.

Ensuite, **test humain au clic** (non automatisable ici) : défilement complet sur téléphone, bouton Rejouer, démo qui sort puis revient à l'écran (Review Focus 5).

- [ ] **Step 6: Reporter les décisions dans la spec**

Dans `docs/superpowers/specs/2026-10-14-landing-animations-design.md` :
- remplacer « dans `<script type="application/json" id="demo-data">` » par « dans des attributs `data-*` sur chaque arrêt (pas de bloc JSON) » ;
- remplacer « Budget : ≤ 60 Ko de JS minifié au total » par « Budget : ≤ 60 Ko de JS transférés (gzip) au total ; Motion seul pèse 49 Ko gzip » ;
- après « La route se redessine vers son nouveau tracé », ajouter « (l'ancienne route s'estompe pendant que la nouvelle se trace : les deux tracés n'ont pas le même nombre de points, un morphing n'est pas possible) ».

- [ ] **Step 7: Commit**

```bash
git add landing/static/js/demo.js landing/static/js/route-scroll.js landing/app/static_src/input.css docs/superpowers/specs/2026-10-14-landing-animations-design.md
git commit -m "feat(landing): animate live demo, route thread, offer and counter"
```
