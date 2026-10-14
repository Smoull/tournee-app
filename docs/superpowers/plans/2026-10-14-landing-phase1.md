# Landing Bouclé.tech, phase 1 (front + API leads mockée) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Une landing Bouclé.tech complète en local (4 variantes métier, formulaire early access, page merci, pages légales) dont l'API `POST /api/leads` est réelle mais stocke en mémoire, Supabase se branchant plus tard sans toucher au front.

**Architecture:** FastAPI + Jinja2 rendus serveur dans `landing/app/`. Les textes vivent dans `app/content/` (un fichier par variante + blocs communs), la validation dans `lead_schema.py`, le stockage derrière un `LeadRepository` (implémentation mémoire choisie explicitement par `LEAD_STORE = "memory"`). Les assets web (woff2, tokens Tailwind) sont dérivés de la source de marque `brand/` par `uv run python -m brand.export`.

**Tech Stack:** Python ≥ 3.12, uv, FastAPI, Jinja2, Pydantic v2 (+ email-validator), uvicorn, pytest + httpx (TestClient), fontTools + brotli (woff2), Tailwind v4 standalone via `pytailwindcss`. Aucune dépendance npm, aucun CDN.

**Spec:** `docs/superpowers/specs/2026-10-12-landing-validation-design.md` · Textes validés : `docs/product/landing-copy.md`

## Global Constraints

- Tout se lance via `uv run` depuis `landing/`. Pas de npm, pas de CDN (polices, JS, CSS auto-hébergés : RGPD).
- TDD obligatoire : test écrit et rouge AVANT le code (cf. `CLAUDE.md`).
- Fail fast : clé de config manquante = erreur au démarrage ; jamais de valeur par défaut silencieuse ni de stockage de secours. `LEAD_STORE` est le seul sélecteur de stockage, aucune bascule automatique.
- Palette (source unique `brand/logo.py` `PALETTE`) : fond `#F4F7F7`, texte `#11181C`, principale `#2A7A6B`, accent `#C67A10`. Aucune 5e teinte (opacités autorisées). Les couleurs par défaut de Tailwind sont désactivées.
- Accent `#C67A10` : CTA, compteur de places, prix early access, logo uniquement. En texte, seulement ≥ 24 px, ou ≥ 18,7 px en gras (contraste 3,2:1 = AA grand texte).
- Typo : Manrope (nom, titres de section, texte courant, prix, formulaire, CTA ; 400/700/800), Fraunces 600 (phrase de douleur H1 uniquement). Pas d'autre police.
- Textes : vouvoiement partout, aucun tiret cadratin `—`, prix toujours affichés HT.
- Infirmier : aucune donnée ni mention de santé (soins, pathologies, traitements).
- Nom affiché `Bouclé` + `.tech` à 50 % de la taille (`SUFFIX_RATIO = 0.5`), accroche « Votre tournée, sans détour. ».
- Aucune donnée personnelle réelle dans les tests (emails `@example.com`, téléphones fictifs) ; jamais d'email ou téléphone dans les logs ni dans les messages d'exception.
- Prix : 29 € HT/mois ; early access 19 € HT/mois à vie ; « 120 € HT économisés chaque année ». N places early access = **10 (valeur mock)** en attendant l'arbitrage marketing.

## Review Focus

1. **Email saisi avec majuscules ou espaces** (`" Jean@Example.com "` puis `jean@example.com`) : doit être reconnu comme doublon (409), pas créer deux leads. → test dans Task 6 (`test_same_email_with_different_case_is_a_duplicate`).
2. **Téléphones FR écrits de mille façons** (`06.12.34.56.78`, `+33 6 12 34 56 78`, `06-12-34-56-78`) : acceptés et normalisés ; numéro tronqué refusé avec un message clair. → test paramétré Task 2.
3. **Compteur à 0 ou à 1 place** : jamais « Plus que 0 places » ni « -3 », pluriel correct à 1. → tests Task 4 (`test_counter_wording`) et Task 7 (`test_counter_decreases_after_a_lead`).
4. **Corps de requête cassé** (JSON invalide, tableau, champ inconnu) : 400 avec message, jamais 500. → tests Task 6.
5. **Double clic sur « Je réserve ma place »** : le bouton est désactivé pendant l'envoi ; un 2e envoi éventuel renvoie 409 « déjà sur la liste », pas une erreur. → vérification manuelle Task 8 (étape run).

---

## File Structure

```
landing/
  pyproject.toml                 (modifié) dépendances
  secret.toml.example            (modifié) LEAD_STORE, CALCOM_URL, CONTACT_EMAIL
  README.md                      (créé) commandes uv
  brand/
    web_fonts.py                 (créé) woff2 subset latin depuis brand/fonts/*.ttf
    theme.py                     (créé) @theme Tailwind généré depuis PALETTE
    export.py                    (modifié) __main__ génère aussi fonts + theme
  app/
    __init__.py
    settings.py                  config secret.toml, fail fast
    lead_schema.py               validation Pydantic du lead
    lead_repository.py           LeadRepository + InMemoryLeadRepository + erreurs
    offer.py                     règles de prix et de places (logique pure)
    content/
      __init__.py                VARIANTS (registre slug -> Variant)
      models.py                  dataclasses Pain, Variant
      commun.py                  blocs communs, options du formulaire, messages UI
      legal.py                   textes mentions légales / confidentialité (mock)
      generique.py, laveur_vitres.py, infirmier.py, services_domicile.py
    routes.py                    pages GET + POST /api/leads
    factory.py                   create_app(settings, repository), build_repository
    main.py                      câblage uvicorn (lit secret.toml)
    templates/ base.html, landing.html, merci.html, legal.html
    static_src/ input.css, theme.css (généré)
  static/
    brand/ (existant)  fonts/ (généré)  css/app.css (généré, gitignoré)  js/lead-form.js
  tests/
    conftest.py, test_settings.py, test_lead_schema.py, test_lead_repository.py,
    test_offer_and_content.py, test_web_assets.py, test_api_leads.py, test_pages.py
```

---

### Task 1: Dépendances, configuration fail fast, mise à jour de la spec

**Files:**
- Modify: `landing/pyproject.toml`, `landing/secret.toml.example`, `.gitignore`, `docs/superpowers/specs/2026-10-12-landing-validation-design.md`
- Create: `landing/app/__init__.py`, `landing/app/settings.py`
- Test: `landing/tests/test_settings.py`

**Interfaces:**
- Produces: `Settings(lead_store: str, calcom_url: str, contact_email: str)` (dataclass frozen), `load_settings(path: Path) -> Settings`, `SettingsError(RuntimeError)`, `SUPPORTED_LEAD_STORES = {"memory"}`.

- [ ] **Step 1: Ajouter les dépendances**

```bash
cd landing
uv add fastapi jinja2 uvicorn email-validator
uv add --dev httpx fonttools brotli pytailwindcss
```

- [ ] **Step 2: Écrire le test qui échoue**

`landing/tests/test_settings.py` :

```python
import pytest

from app.settings import Settings, SettingsError, load_settings

VALID = 'LEAD_STORE = "memory"\nCALCOM_URL = "https://cal.com/example/15min"\nCONTACT_EMAIL = "contact@example.com"\n'


def test_loads_valid_settings(tmp_path):
    path = tmp_path / "secret.toml"
    path.write_text(VALID)

    assert load_settings(path) == Settings(
        lead_store="memory",
        calcom_url="https://cal.com/example/15min",
        contact_email="contact@example.com",
    )


def test_missing_file_fails_with_hint(tmp_path):
    with pytest.raises(SettingsError, match="secret.toml.example"):
        load_settings(tmp_path / "secret.toml")


@pytest.mark.parametrize("key", ["LEAD_STORE", "CALCOM_URL", "CONTACT_EMAIL"])
def test_missing_or_empty_key_fails(tmp_path, key):
    path = tmp_path / "secret.toml"
    path.write_text(VALID.replace(f'{key} = "', f'{key} = "" #'))

    with pytest.raises(SettingsError, match=key):
        load_settings(path)


def test_unsupported_lead_store_fails(tmp_path):
    path = tmp_path / "secret.toml"
    path.write_text(VALID.replace('"memory"', '"supabase"'))

    with pytest.raises(SettingsError, match="supabase"):
        load_settings(path)
```

- [ ] **Step 3: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_settings.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: Implémenter**

`landing/app/__init__.py` : fichier vide.

`landing/app/settings.py` :

```python
import tomllib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_KEYS = ("LEAD_STORE", "CALCOM_URL", "CONTACT_EMAIL")
SUPPORTED_LEAD_STORES = {"memory"}


class SettingsError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    lead_store: str
    calcom_url: str
    contact_email: str


def load_settings(path: Path) -> Settings:
    if not path.exists():
        raise SettingsError(f"{path} introuvable : copiez secret.toml.example en secret.toml")
    with path.open("rb") as file:
        raw = tomllib.load(file)

    missing = [key for key in REQUIRED_KEYS if not raw.get(key)]
    if missing:
        raise SettingsError(f"Clés manquantes ou vides dans {path.name} : {', '.join(missing)}")
    if raw["LEAD_STORE"] not in SUPPORTED_LEAD_STORES:
        raise SettingsError(f"LEAD_STORE={raw['LEAD_STORE']!r} non supporté en phase 1 (valeur attendue : 'memory')")

    return Settings(lead_store=raw["LEAD_STORE"], calcom_url=raw["CALCOM_URL"], contact_email=raw["CONTACT_EMAIL"])
```

- [ ] **Step 5: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: tous les tests PASS (y compris `test_brand.py`).

- [ ] **Step 6: Mettre à jour `secret.toml.example`, `.gitignore` et la spec**

`landing/secret.toml.example` (remplacer tout le fichier) :

```toml
# Copier en secret.toml (gitignoré) et remplir. En prod : variables GitLab LANDING_* du repo infra.
# Stockage des leads : "memory" (phase 1, leads perdus au redémarrage). "supabase" arrive en phase 2.
LEAD_STORE = "memory"
CALCOM_URL = "https://cal.com/example/15min"
CONTACT_EMAIL = "contact@example.com"

# Phase 2 (non lus en phase 1) :
# SUPABASE_URL = "https://example.supabase.co"
# Clé anon/publishable uniquement : RLS = INSERT seul. Jamais service_role.
# SUPABASE_ANON_KEY = "changeme"
# POSTHOG_KEY = "phc_changeme"
# POSTHOG_HOST = "https://eu.i.posthog.com"
```

Ajouter à `.gitignore` (racine) la ligne :

```
landing/static/css/
```

Dans la spec, remplacer les lignes 56-57 (« Nombre de places early access N : **à définir** … Le compteur reste bloqué tant que N n'est pas fixé. ») par :

```markdown
Nombre de places early access N : **à définir** (arbitrage marketing : global vs par variante).
Phase 1 : N = 10 (valeur mock, `app/offer.py`), compteur = N - leads stockés, jamais négatif.
Phase 2 : le rôle `anon` ne peut pas compter les leads (RLS INSERT seul) → fonction Postgres
`security definer` `places_restantes()` exécutable par `anon`, qui ne renvoie qu'un entier.
```

Et remplacer la puce Motion de la section Design par :

```markdown
- **Pas de Motion en phase 1** : une seule animation (la route du logo se trace au chargement) en CSS pur,
  désactivée si `prefers-reduced-motion`. Motion (MIT, auto-hébergé) seulement si un besoin réel apparaît.
```

Et ajouter sous la section Analytics :

```markdown
Phase 1 (local, sans trafic) : PostHog non branché. Branchement en phase 2 avec l'hébergement.
```

Et dans la section Architecture, sous « Responsabilités », ajouter :

```markdown
  - `lead_repository.py` expose `LeadRepository` ; phase 1 : `InMemoryLeadRepository` choisi
    explicitement par `LEAD_STORE = "memory"` (aucune bascule automatique)
  - `offer.py` : prix et places (seul endroit si l'offre change)
```

- [ ] **Step 7: Commit**

```bash
git add landing/pyproject.toml landing/uv.lock landing/secret.toml.example landing/app .gitignore landing/tests/test_settings.py docs/superpowers/specs/2026-10-12-landing-validation-design.md
git commit -m "feat(landing): fail-fast settings and phase 1 dependencies"
```

---

### Task 2: Schéma du lead (validation + normalisation)

**Files:**
- Create: `landing/app/lead_schema.py`
- Test: `landing/tests/test_lead_schema.py`

**Interfaces:**
- Produces: `LeadIn` (Pydantic, champs ci-dessous), `invalid_fields(error: ValidationError) -> set[str]`, types `Metier`, `Taille`, `Douleur`, `Variante` (`Literal`).
- `LeadIn` : `metier: Metier`, `taille: Taille`, `douleur: Douleur`, `email: str` (minuscules), `phone: str` (E.164 `+33XXXXXXXXX`), `accepte_appel: bool = False`, `consentement_rgpd: Literal[True]`, `website: str = ""` (honeypot, doit rester vide), `variante: Variante`, `utm_source: str | None`, `utm_campaign: str | None` (≤ 100 car.).

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_lead_schema.py` :

```python
import pytest
from pydantic import ValidationError

from app.lead_schema import LeadIn, invalid_fields

VALID = {
    "metier": "laveur-vitres",
    "taille": "solo",
    "douleur": "imprevus",
    "email": "jean.dupont@example.com",
    "phone": "06 12 34 56 78",
    "accepte_appel": True,
    "consentement_rgpd": True,
    "website": "",
    "variante": "laveur-vitres",
}


def errors_for(payload: dict) -> set[str]:
    with pytest.raises(ValidationError) as error:
        LeadIn.model_validate(payload)
    return invalid_fields(error.value)


def test_valid_lead_is_accepted():
    lead = LeadIn.model_validate(VALID)
    assert lead.metier == "laveur-vitres"
    assert lead.accepte_appel is True


@pytest.mark.parametrize("field", ["metier", "taille", "douleur", "email", "phone", "consentement_rgpd", "variante"])
def test_required_field_missing(field):
    payload = {key: value for key, value in VALID.items() if key != field}
    assert field in errors_for(payload)


def test_accepte_appel_is_optional():
    payload = {key: value for key, value in VALID.items() if key != "accepte_appel"}
    assert LeadIn.model_validate(payload).accepte_appel is False


def test_consent_false_is_refused():
    assert "consentement_rgpd" in errors_for({**VALID, "consentement_rgpd": False})


@pytest.mark.parametrize("field,value", [("metier", "plombier"), ("taille", "12"), ("douleur", "ennui"), ("variante", "x")])
def test_unknown_choice_is_refused(field, value):
    assert field in errors_for({**VALID, field: value})


def test_email_is_trimmed_and_lowercased():
    assert LeadIn.model_validate({**VALID, "email": "  Jean.Dupont@Example.COM "}).email == "jean.dupont@example.com"


def test_invalid_email_is_refused():
    assert "email" in errors_for({**VALID, "email": "jean.dupont@"})


@pytest.mark.parametrize(
    "raw", ["0612345678", "06 12 34 56 78", "06.12.34.56.78", "06-12-34-56-78", "+33 6 12 34 56 78", "+33612345678"]
)
def test_french_phone_formats_are_normalized(raw):
    assert LeadIn.model_validate({**VALID, "phone": raw}).phone == "+33612345678"


@pytest.mark.parametrize("raw", ["06 12 34", "0012345678", "+44 7911 123456", "06 12 34 56 78 90", "téléphone"])
def test_invalid_phone_is_refused(raw):
    assert "phone" in errors_for({**VALID, "phone": raw})


def test_filled_honeypot_is_refused():
    assert "website" in errors_for({**VALID, "website": "https://spam.example"})


def test_unknown_field_is_refused():
    assert "admin" in errors_for({**VALID, "admin": True})


def test_too_long_utm_is_refused():
    assert "utm_source" in errors_for({**VALID, "utm_source": "a" * 101})


def test_non_object_payload_has_no_field_errors():
    assert errors_for([VALID]) == set()
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_lead_schema.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app.lead_schema'`

- [ ] **Step 3: Implémenter**

`landing/app/lead_schema.py` :

```python
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator

Metier = Literal["laveur-vitres", "infirmier", "aide-domicile", "jardinier", "ramoneur", "autre"]
Taille = Literal["solo", "2-5", "6+"]
Douleur = Literal["imprevus", "rentabilite", "planning", "coordination", "autre"]
Variante = Literal["generique", "laveur-vitres", "infirmier", "services-domicile"]

FRENCH_PHONE = re.compile(r"^(?:\+33|0)([1-9]\d{8})$")
PHONE_SEPARATORS = re.compile(r"[\s.\-]")


class LeadIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metier: Metier
    taille: Taille
    douleur: Douleur
    email: EmailStr
    phone: str
    accepte_appel: bool = False
    consentement_rgpd: Literal[True]
    website: str = Field(default="", max_length=0)
    variante: Variante
    utm_source: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str) -> str:
        return email.lower()

    @field_validator("phone")
    @classmethod
    def normalize_french_phone(cls, phone: str) -> str:
        match = FRENCH_PHONE.match(PHONE_SEPARATORS.sub("", phone))
        if match is None:
            raise ValueError("numéro de téléphone français invalide")
        return "+33" + match.group(1)


def invalid_fields(error: ValidationError) -> set[str]:
    return {str(detail["loc"][0]) for detail in error.errors() if detail["loc"]}
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest tests/test_lead_schema.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add landing/app/lead_schema.py landing/tests/test_lead_schema.py
git commit -m "feat(landing): lead schema with FR phone and email normalization"
```

---

### Task 3: Repository des leads (mémoire)

**Files:**
- Create: `landing/app/lead_repository.py`
- Test: `landing/tests/test_lead_repository.py`

**Interfaces:**
- Consumes: `LeadIn` (Task 2).
- Produces: `LeadRepository` (Protocol : `add(lead: LeadIn) -> None`, `count() -> int`), `InMemoryLeadRepository`, `DuplicateLeadError(Exception)`, `StorageUnavailableError(Exception)`. Les exceptions ne contiennent jamais l'email (RGPD : pas de PII dans les logs).

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_lead_repository.py` :

```python
import pytest

from app.lead_repository import DuplicateLeadError, InMemoryLeadRepository
from app.lead_schema import LeadIn

PAYLOAD = {
    "metier": "infirmier",
    "taille": "2-5",
    "douleur": "planning",
    "email": "marie.martin@example.com",
    "phone": "0698765432",
    "consentement_rgpd": True,
    "variante": "infirmier",
}


def test_add_then_count():
    repository = InMemoryLeadRepository()
    repository.add(LeadIn.model_validate(PAYLOAD))
    assert repository.count() == 1


def test_duplicate_email_is_refused_without_leaking_it():
    repository = InMemoryLeadRepository()
    repository.add(LeadIn.model_validate(PAYLOAD))

    with pytest.raises(DuplicateLeadError) as error:
        repository.add(LeadIn.model_validate({**PAYLOAD, "email": "Marie.Martin@Example.com"}))

    assert "marie" not in str(error.value).lower()
    assert repository.count() == 1
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_lead_repository.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app.lead_repository'`

- [ ] **Step 3: Implémenter**

`landing/app/lead_repository.py` :

```python
from typing import Protocol

from app.lead_schema import LeadIn


class DuplicateLeadError(Exception):
    pass


class StorageUnavailableError(Exception):
    pass


class LeadRepository(Protocol):
    def add(self, lead: LeadIn) -> None: ...

    def count(self) -> int: ...


class InMemoryLeadRepository:
    def __init__(self) -> None:
        self._leads: dict[str, LeadIn] = {}

    def add(self, lead: LeadIn) -> None:
        if lead.email in self._leads:
            raise DuplicateLeadError("email déjà inscrit")
        self._leads[lead.email] = lead

    def count(self) -> int:
        return len(self._leads)
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest tests/test_lead_repository.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add landing/app/lead_repository.py landing/tests/test_lead_repository.py
git commit -m "feat(landing): in-memory lead repository"
```

---

### Task 4: Offre et contenus (4 variantes + blocs communs + légal)

**Files:**
- Create: `landing/app/offer.py`, `landing/app/content/__init__.py`, `landing/app/content/models.py`, `landing/app/content/commun.py`, `landing/app/content/legal.py`, `landing/app/content/generique.py`, `landing/app/content/laveur_vitres.py`, `landing/app/content/infirmier.py`, `landing/app/content/services_domicile.py`
- Test: `landing/tests/test_offer_and_content.py`

**Interfaces:**
- Consumes: `Metier`, `Taille`, `Douleur`, `Variante` (Task 2).
- Produces:
  - `offer.PRIX_HT = 29`, `offer.PRIX_EARLY_ACCESS_HT = 19`, `offer.PLACES_EARLY_ACCESS = 10`, `offer.economie_annuelle_ht() -> int`, `offer.places_restantes(inscrits: int) -> int`.
  - `content.models.Pain(probleme: str, solution: str)`, `content.models.Variant(slug: str, path: str, metier_prefill: str | None, h1: str, sous_titre: str, douleurs: tuple[Pain, Pain, Pain])`.
  - `content.VARIANTS: dict[str, Variant]` (clé = slug).
  - `content.commun` : `CTA`, `SOUS_CTA`, `UTILITE_TITRE`, `FAISABILITE_TITRE`, `FAISABILITE`, `MORALE_TITRE`, `MORALE`, `OPPORTUNITE_TITRE`, `PRIX_NORMAL`, `PRIX_EARLY`, `ECONOMIE`, `ATTENTE`, `compteur(places: int) -> str`, `FORMULAIRE_TITRE`, `FORMULAIRE_INTRO`, `METIERS`, `TAILLES`, `DOULEURS`, `LABELS`, `CONSENTEMENT`, `ACCEPTE_APPEL`, `FIELD_MESSAGES`, `FORMULAIRE_INVALIDE`, `DEJA_INSCRIT`, `INDISPONIBLE` (gabarit `{contact_email}`), `MERCI_TITRE`, `MERCI_TEXTE`, `MERCI_APPEL`, `MERCI_LIEN`.
  - `content.legal.PAGES: dict[str, tuple[str, tuple[str, ...]]]` (clé = chemin URL, valeur = (titre, paragraphes)).

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_offer_and_content.py` :

```python
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
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_offer_and_content.py -q`
Expected: FAIL `ImportError: cannot import name 'offer' from 'app'`

- [ ] **Step 3: Implémenter l'offre**

`landing/app/offer.py` :

```python
PRIX_HT = 29
PRIX_EARLY_ACCESS_HT = 19
# Valeur mock : N sera fixé par l'arbitrage marketing (cf. spec, section Opportunité).
PLACES_EARLY_ACCESS = 10


def economie_annuelle_ht() -> int:
    return (PRIX_HT - PRIX_EARLY_ACCESS_HT) * 12


def places_restantes(inscrits: int) -> int:
    return max(PLACES_EARLY_ACCESS - inscrits, 0)
```

- [ ] **Step 4: Implémenter les modèles et les contenus**

`landing/app/content/models.py` :

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Pain:
    probleme: str
    solution: str


@dataclass(frozen=True)
class Variant:
    slug: str
    path: str
    metier_prefill: str | None
    h1: str
    sous_titre: str
    douleurs: tuple[Pain, Pain, Pain]
```

`landing/app/content/generique.py` :

```python
from app.content.models import Pain, Variant

VARIANT = Variant(
    slug="generique",
    path="/",
    metier_prefill=None,
    h1="Un imprévu à 7h, et toute la journée déraille ?",
    sous_titre="Bouclé recalcule votre tournée et prévient vos clients par SMS. Vous, vous conduisez.",
    douleurs=(
        Pain(
            "Un client annule, un autre ajoute un passage.",
            "Votre tournée se réorganise en un geste. Les clients concernés reçoivent leur nouvel horaire par SMS.",
        ),
        Pain(
            "Des kilomètres en trop, sans s'en rendre compte.",
            "Bouclé ordonne vos arrêts et chiffre le coût de chaque journée : carburant, temps, rentabilité.",
        ),
        Pain(
            "Le planning de la semaine tient dans votre tête.",
            "Il tient sur une page : imprimable chaque matin, partageable avec vos collègues.",
        ),
    ),
)
```

`landing/app/content/laveur_vitres.py` :

```python
from app.content.models import Pain, Variant

VARIANT = Variant(
    slug="laveur-vitres",
    path="/laveur-vitres",
    metier_prefill="laveur-vitres",
    h1="Un client annule à 7h ?",
    sous_titre="Votre tournée se recalcule, vos clients sont prévenus par SMS. Vous gardez votre matinée.",
    douleurs=(
        Pain(
            "La pluie décale toute la journée.",
            "Reportez en un geste : Bouclé repropose les créneaux et prévient chaque client.",
        ),
        Pain(
            "Les passages tous les 2 mois, il faut s'en souvenir.",
            "Les clients récurrents reviennent tout seuls dans votre planning, au bon rythme.",
        ),
        Pain(
            "Porte fermée, client absent, trajet pour rien.",
            "La veille, un SMS confirme le passage. Le client absent se signale avant, pas après.",
        ),
    ),
)
```

`landing/app/content/infirmier.py` :

```python
from app.content.models import Pain, Variant

# Aucune donnée ni mention de santé : on parle de tournée, d'horaires et de trajets (cf. spec, HDS).
VARIANT = Variant(
    slug="infirmier",
    path="/infirmier",
    metier_prefill="infirmier",
    h1="Un passage ajouté en dernière minute, et toute la tournée glisse ?",
    sous_titre=(
        "Bouclé réorganise votre tournée en respectant vos horaires fixes, "
        "et prévient vos patients de l'heure de passage."
    ),
    douleurs=(
        Pain(
            "Des passages à heure fixe à tenir coûte que coûte.",
            "Vous les verrouillez : Bouclé organise le reste de la tournée autour.",
        ),
        Pain(
            "Un patient absent ou un remplacement imprévu.",
            "La tournée se recalcule, les patients suivants reçoivent leur nouvel horaire par SMS.",
        ),
        Pain(
            "Les kilomètres du cabinet, mal répartis.",
            "Une vue claire des trajets de la journée, imprimable, partageable avec vos collègues ou votre remplaçante.",
        ),
    ),
)
```

`landing/app/content/services_domicile.py` :

```python
from app.content.models import Pain, Variant

VARIANT = Variant(
    slug="services-domicile",
    path="/services-domicile",
    metier_prefill=None,
    h1="Trois clients à caser, un seul après-midi ?",
    sous_titre="Bouclé trouve le bon ordre de passage et prévient vos clients par SMS. Vous arrivez à l'heure, sans courir.",
    douleurs=(
        Pain(
            "Les demandes arrivent en vrac, au téléphone.",
            "Ajoutez-les en quelques secondes : Bouclé leur trouve une place dans la semaine.",
        ),
        Pain(
            "Les pics de saison (taille, ramonage, entretien) débordent.",
            "Bouclé répartit les passages sur plusieurs semaines, sans oublier personne.",
        ),
        Pain(
            "Plusieurs intervenants, qui va où ?",
            "Chacun reçoit sa tournée, vous gardez la vue d'ensemble.",
        ),
    ),
)
```

`landing/app/content/commun.py` :

```python
from app.offer import PLACES_EARLY_ACCESS, PRIX_EARLY_ACCESS_HT, PRIX_HT, economie_annuelle_ht

CTA = "Je réserve ma place"
SOUS_CTA = f"{PRIX_EARLY_ACCESS_HT} € HT/mois à vie pour les {PLACES_EARLY_ACCESS} premiers."

UTILITE_TITRE = "Ce que Bouclé change dans votre journée"

FAISABILITE_TITRE = "On configure tout pour vous"
FAISABILITE = (
    ("Prise en main en 5 minutes.", "On importe vos clients avec vous, au téléphone si besoin."),
    ("Votre tournée sur papier.", "Un PDF clair, imprimable chaque matin."),
    ("Vous gardez la main.", "Bouclé propose, vous validez ou vous modifiez. Toujours."),
)

MORALE_TITRE = "Vos données restent les vôtres"
MORALE = (
    ("Hébergées en France.", "Jamais revendues, jamais partagées."),
    ("Vos clients respectés.", "Prévenus avant, jamais surpris par un retard."),
    ("Du temps rendu.", "Moins de trajets et de coups de fil, plus de soirées pour vous et vos proches."),
)

OPPORTUNITE_TITRE = "Early access : le prix des premiers, à vie"
PRIX_NORMAL = f"{PRIX_HT} € HT/mois"
PRIX_EARLY = f"{PRIX_EARLY_ACCESS_HT} € HT/mois à vie"
ECONOMIE = f"-{PRIX_HT - PRIX_EARLY_ACCESS_HT} € HT/mois à vie, soit {economie_annuelle_ht()} € HT économisés chaque année."
ATTENTE = (
    f"Après les {PLACES_EARLY_ACCESS} premières places, le tarif passe à {PRIX_HT} € HT/mois. "
    "Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui."
)


def compteur(places: int) -> str:
    if places == 0:
        return "Toutes les places early access sont prises : inscrivez-vous pour la liste d'attente."
    if places == 1:
        return "Plus qu'une place au tarif early access."
    return f"Plus que {places} places au tarif early access."


FORMULAIRE_TITRE = "Réservez votre place"
FORMULAIRE_INTRO = "30 secondes. Aucun paiement aujourd'hui."

METIERS = (
    ("laveur-vitres", "Laveur de vitres"),
    ("infirmier", "Infirmier ou infirmière libérale"),
    ("aide-domicile", "Aide à domicile"),
    ("jardinier", "Jardinier, paysagiste"),
    ("ramoneur", "Ramoneur"),
    ("autre", "Autre métier en tournée"),
)
TAILLES = (("solo", "Seul(e)"), ("2-5", "2 à 5"), ("6+", "6 et plus"))
DOULEURS = (
    ("imprevus", "Les imprévus"),
    ("rentabilite", "La rentabilité"),
    ("planning", "Le planning"),
    ("coordination", "La coordination"),
    ("autre", "Autre chose"),
)
LABELS = {
    "metier": "Votre métier",
    "taille": "Votre équipe",
    "douleur": "Ce qui vous pèse le plus",
    "email": "Votre email",
    "phone": "Votre téléphone",
}
ACCEPTE_APPEL = "J'accepte un appel de 15 minutes pour parler de ma tournée."
CONSENTEMENT = "J'accepte que Bouclé.tech utilise ces informations pour me recontacter au sujet de l'early access."

FIELD_MESSAGES = {
    "metier": "Choisissez votre métier.",
    "taille": "Indiquez la taille de votre équipe.",
    "douleur": "Choisissez ce qui vous pèse le plus.",
    "email": "Cet email ne semble pas valide.",
    "phone": "Ce numéro ne semble pas complet.",
    "consentement_rgpd": "Votre accord est nécessaire pour que nous puissions vous recontacter.",
}
FORMULAIRE_INVALIDE = "Le formulaire n'a pas pu être envoyé. Rechargez la page et réessayez."
DEJA_INSCRIT = "Vous êtes déjà sur la liste. À très vite !"
INDISPONIBLE = "Une erreur est survenue, réessayez dans un instant. Ou écrivez-nous : {contact_email}"

MERCI_TITRE = "C'est bouclé."
MERCI_TEXTE = f"Votre place early access est réservée : {PRIX_EARLY_ACCESS_HT} € HT/mois à vie."
MERCI_APPEL = "On vous recontacte très vite. Pour aller plus vite, réservez un appel de 15 minutes."
MERCI_LIEN = "Choisir un créneau"
```

`landing/app/content/legal.py` :

```python
# Mock phase 1 : identité de l'éditeur et hébergeur à compléter avant mise en ligne (phase 2).
PAGES = {
    "/mentions-legales": (
        "Mentions légales",
        (
            "Éditeur : à compléter avant mise en ligne (nom, statut, SIRET, adresse, directeur de publication).",
            "Hébergement : à compléter avant mise en ligne (hébergeur, adresse).",
            "Contact : voir l'adresse en bas de page.",
        ),
    ),
    "/confidentialite": (
        "Politique de confidentialité",
        (
            "Finalité : vous recontacter au sujet de l'early access de Bouclé.tech et, si vous l'acceptez, "
            "convenir d'un appel de 15 minutes.",
            "Données collectées : métier, taille d'équipe, principale difficulté, email, téléphone, "
            "source de la visite. Aucune donnée de santé.",
            "Durée de conservation : 12 mois sans suite, puis suppression.",
            "Vos droits : accès, rectification et suppression sur simple demande à l'adresse en bas de page.",
            "Vos données ne sont jamais revendues ni partagées.",
        ),
    ),
}
```

`landing/app/content/__init__.py` :

```python
from app.content import generique, infirmier, laveur_vitres, services_domicile
from app.content.models import Variant

VARIANTS: dict[str, Variant] = {
    module.VARIANT.slug: module.VARIANT for module in (generique, laveur_vitres, infirmier, services_domicile)
}
```

- [ ] **Step 5: Lancer, vérifier le vert**

Run: `uv run pytest tests/test_offer_and_content.py -q`
Expected: PASS (le dossier `templates/` n'existe pas encore : `glob` renvoie une liste vide, il sera couvert en Task 7).

- [ ] **Step 6: Commit**

```bash
git add landing/app/offer.py landing/app/content landing/tests/test_offer_and_content.py
git commit -m "feat(landing): offer rules and validated copy for 4 variants"
```

---

### Task 5: Assets web dérivés de la marque (woff2 + tokens Tailwind)

**Files:**
- Create: `landing/brand/web_fonts.py`, `landing/brand/theme.py`
- Modify: `landing/brand/export.py` (bloc `__main__` uniquement)
- Test: `landing/tests/test_web_assets.py`

**Interfaces:**
- Consumes: `brand.logo.PALETTE`, `brand/fonts/Manrope.ttf`, `brand/fonts/Fraunces.ttf`.
- Produces: `brand.web_fonts.export_web_fonts(out_dir: Path) -> None` (écrit `manrope.woff2` variable 400-800 et `fraunces.woff2` statique 600, subset latin), `brand.theme.theme_css() -> str` (bloc `@theme` Tailwind v4 qui efface les couleurs par défaut). `uv run python -m brand.export` écrit `static/brand/`, `static/fonts/` et `app/static_src/theme.css`.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_web_assets.py` :

```python
from fontTools.ttLib import TTFont

from brand.logo import PALETTE
from brand.theme import theme_css
from brand.web_fonts import export_web_fonts


def test_web_fonts_are_latin_woff2_with_expected_weights(tmp_path):
    export_web_fonts(tmp_path)

    manrope = TTFont(tmp_path / "manrope.woff2")
    fraunces = TTFont(tmp_path / "fraunces.woff2")
    for font in (manrope, fraunces):
        assert font.flavor == "woff2"
        cmap = font.getBestCmap()
        for character in "éèàçœ€’ÉÀ":
            assert ord(character) in cmap, character
        assert ord("Ж") not in cmap

    weight_axis = next(axis for axis in manrope["fvar"].axes if axis.axisTag == "wght")
    assert (weight_axis.minValue, weight_axis.maxValue) == (400, 800)
    assert "fvar" not in fraunces


def test_theme_exposes_only_the_palette():
    css = theme_css()
    assert css.startswith("@theme {")
    assert "--color-*: initial;" in css
    for name, color in PALETTE.items():
        assert f"--color-{name}: {color};" in css
    assert '--font-sans: "Manrope"' in css
    assert '--font-douleur: "Fraunces"' in css
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_web_assets.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'brand.theme'`

- [ ] **Step 3: Implémenter**

`landing/brand/theme.py` :

```python
from brand.logo import PALETTE


def theme_css() -> str:
    colors = "\n".join(f"  --color-{name}: {color};" for name, color in PALETTE.items())
    # --color-*: initial retire la palette par défaut de Tailwind : impossible d'utiliser une 5e teinte.
    return (
        "@theme {\n"
        "  --color-*: initial;\n"
        f"{colors}\n"
        '  --font-sans: "Manrope", system-ui, sans-serif;\n'
        '  --font-douleur: "Fraunces", Georgia, serif;\n'
        "}\n"
    )
```

`landing/brand/web_fonts.py` :

```python
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS_DIR = Path(__file__).parent / "fonts"
LATIN_UNICODES = (
    "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,"
    "U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
)
# None = axe figé à sa valeur par défaut.
WEB_FONTS = {
    "manrope.woff2": ("Manrope.ttf", {"wght": (400, 800)}),
    "fraunces.woff2": ("Fraunces.ttf", {"wght": 600, "opsz": None, "SOFT": None, "WONK": None}),
}


def export_web_fonts(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for output_name, (source_name, axis_limits) in WEB_FONTS.items():
        font = instancer.instantiateVariableFont(TTFont(FONTS_DIR / source_name), axis_limits)
        options = subset.Options()
        options.layout_features = ["*"]
        subsetter = subset.Subsetter(options)
        subsetter.populate(unicodes=subset.parse_unicodes(LATIN_UNICODES))
        subsetter.subset(font)
        font.flavor = "woff2"
        font.save(out_dir / output_name)
```

Dans `landing/brand/export.py`, remplacer le bloc final :

```python
if __name__ == "__main__":
    export_brand_assets(Path(__file__).parent.parent / "static" / "brand")
```

par :

```python
if __name__ == "__main__":
    landing_dir = Path(__file__).parent.parent
    export_brand_assets(landing_dir / "static" / "brand")
    export_web_fonts(landing_dir / "static" / "fonts")
    (landing_dir / "app" / "static_src").mkdir(parents=True, exist_ok=True)
    (landing_dir / "app" / "static_src" / "theme.css").write_text(theme_css())
```

et ajouter en tête de `export.py`, avec les autres imports `brand.*` :

```python
from brand.theme import theme_css
from brand.web_fonts import export_web_fonts
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Générer les assets**

Run: `uv run python -m brand.export && ls static/fonts app/static_src`
Expected: `fraunces.woff2  manrope.woff2` et `theme.css`

- [ ] **Step 6: Commit**

```bash
git add landing/brand landing/static/fonts landing/app/static_src/theme.css landing/tests/test_web_assets.py
git commit -m "feat(landing): latin woff2 fonts and Tailwind theme derived from brand"
```

---

### Task 6: API `POST /api/leads`

**Files:**
- Create: `landing/app/routes.py`, `landing/app/factory.py`, `landing/tests/conftest.py`
- Test: `landing/tests/test_api_leads.py`

**Interfaces:**
- Consumes: `Settings` (T1), `LeadIn`, `invalid_fields` (T2), `LeadRepository`, `InMemoryLeadRepository`, `DuplicateLeadError`, `StorageUnavailableError` (T3), `content.commun` (T4).
- Produces:
  - `factory.create_app(settings: Settings, repository: LeadRepository) -> FastAPI`, `factory.build_repository(settings: Settings) -> LeadRepository`.
  - `routes.build_router(settings, repository, templates) -> APIRouter`.
  - Contrat HTTP : `201 {"redirect": "/merci"}` · `400 {"errors": {champ: message}, "message": str?}` · `409 {"message": DEJA_INSCRIT}` · `503 {"message": INDISPONIBLE formaté}`.
  - Fixtures pytest : `settings`, `repository`, `client`, `lead_payload`.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/conftest.py` :

```python
import pytest
from fastapi.testclient import TestClient

from app.factory import create_app
from app.lead_repository import InMemoryLeadRepository
from app.settings import Settings


@pytest.fixture
def settings():
    return Settings(lead_store="memory", calcom_url="https://cal.com/example/15min", contact_email="contact@example.com")


@pytest.fixture
def repository():
    return InMemoryLeadRepository()


@pytest.fixture
def client(settings, repository):
    return TestClient(create_app(settings, repository))


@pytest.fixture
def lead_payload():
    return {
        "metier": "jardinier",
        "taille": "solo",
        "douleur": "rentabilite",
        "email": "paul.durand@example.com",
        "phone": "07 11 22 33 44",
        "accepte_appel": False,
        "consentement_rgpd": True,
        "website": "",
        "variante": "services-domicile",
        "utm_source": "agence",
        "utm_campaign": "lancement",
    }
```

`landing/tests/test_api_leads.py` :

```python
from fastapi.testclient import TestClient

from app.content import commun
from app.factory import build_repository, create_app
from app.lead_repository import InMemoryLeadRepository, StorageUnavailableError


class UnavailableRepository:
    def add(self, lead) -> None:
        raise StorageUnavailableError("stockage injoignable")

    def count(self) -> int:
        return 0


def test_valid_lead_is_stored(client, repository, lead_payload):
    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 201
    assert response.json() == {"redirect": "/merci"}
    assert repository.count() == 1


def test_invalid_fields_return_french_messages(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "phone": "06 12", "email": "paul@"})

    assert response.status_code == 400
    assert response.json()["errors"] == {
        "phone": commun.FIELD_MESSAGES["phone"],
        "email": commun.FIELD_MESSAGES["email"],
    }
    assert repository.count() == 0


def test_missing_consent_is_refused(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "consentement_rgpd": False})

    assert response.status_code == 400
    assert response.json()["errors"] == {"consentement_rgpd": commun.FIELD_MESSAGES["consentement_rgpd"]}
    assert repository.count() == 0


def test_honeypot_stores_nothing_and_reveals_nothing(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "website": "https://spam.example"})

    assert response.status_code == 400
    assert response.json() == {"errors": {}, "message": commun.FORMULAIRE_INVALIDE}
    assert repository.count() == 0


def test_duplicate_returns_409(client, lead_payload):
    client.post("/api/leads", json=lead_payload)
    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 409
    assert response.json() == {"message": commun.DEJA_INSCRIT}


def test_same_email_with_different_case_is_a_duplicate(client, repository, lead_payload):
    client.post("/api/leads", json=lead_payload)
    response = client.post("/api/leads", json={**lead_payload, "email": "  Paul.Durand@Example.com "})

    assert response.status_code == 409
    assert repository.count() == 1


def test_storage_down_returns_503_with_contact_email(settings, lead_payload):
    client = TestClient(create_app(settings, UnavailableRepository()))

    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 503
    assert response.json() == {"message": commun.INDISPONIBLE.format(contact_email="contact@example.com")}


def test_malformed_json_returns_400(client):
    response = client.post("/api/leads", content=b"{pas du json", headers={"Content-Type": "application/json"})

    assert response.status_code == 400
    assert response.json()["message"] == commun.FORMULAIRE_INVALIDE


def test_non_object_body_returns_400(client, lead_payload):
    response = client.post("/api/leads", json=[lead_payload])

    assert response.status_code == 400
    assert response.json()["message"] == commun.FORMULAIRE_INVALIDE


def test_unknown_field_returns_400(client, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "admin": True})

    assert response.status_code == 400
    assert response.json()["errors"] == {"admin": commun.FORMULAIRE_INVALIDE}


def test_memory_store_is_built_from_settings(settings):
    assert isinstance(build_repository(settings), InMemoryLeadRepository)
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_api_leads.py -q`
Expected: FAIL `ModuleNotFoundError: No module named 'app.factory'`

- [ ] **Step 3: Implémenter**

`landing/app/routes.py` :

```python
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.content import commun
from app.lead_repository import DuplicateLeadError, LeadRepository, StorageUnavailableError
from app.lead_schema import LeadIn, invalid_fields
from app.settings import Settings


def build_router(settings: Settings, repository: LeadRepository, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.post("/api/leads")
    async def create_lead(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except ValueError:
            return _invalid_form()

        try:
            lead = LeadIn.model_validate(payload)
        except ValidationError as error:
            fields = invalid_fields(error)
            # Honeypot rempli ou corps non exploitable : réponse neutre, rien n'est révélé au robot.
            if not fields or "website" in fields:
                return _invalid_form()
            errors = {field: commun.FIELD_MESSAGES.get(field, commun.FORMULAIRE_INVALIDE) for field in fields}
            return JSONResponse({"errors": errors}, status_code=400)

        try:
            repository.add(lead)
        except DuplicateLeadError:
            return JSONResponse({"message": commun.DEJA_INSCRIT}, status_code=409)
        except StorageUnavailableError:
            message = commun.INDISPONIBLE.format(contact_email=settings.contact_email)
            return JSONResponse({"message": message}, status_code=503)

        return JSONResponse({"redirect": "/merci"}, status_code=201)

    return router


def _invalid_form() -> JSONResponse:
    return JSONResponse({"errors": {}, "message": commun.FORMULAIRE_INVALIDE}, status_code=400)
```

`landing/app/factory.py` :

```python
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.lead_repository import InMemoryLeadRepository, LeadRepository
from app.routes import build_router
from app.settings import Settings, SettingsError

LANDING_DIR = Path(__file__).parent.parent
logger = logging.getLogger(__name__)


def build_repository(settings: Settings) -> LeadRepository:
    if settings.lead_store == "memory":
        logger.warning("LEAD_STORE=memory : les leads sont perdus à chaque redémarrage.")
        return InMemoryLeadRepository()
    raise SettingsError(f"LEAD_STORE={settings.lead_store!r} non supporté")


def create_app(settings: Settings, repository: LeadRepository) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=LANDING_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=LANDING_DIR / "app" / "templates")
    app.include_router(build_router(settings, repository, templates))
    return app
```

- [ ] **Step 4: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add landing/app/routes.py landing/app/factory.py landing/tests/conftest.py landing/tests/test_api_leads.py
git commit -m "feat(landing): POST /api/leads with 201/400/409/503 contract"
```

---

### Task 7: Pages HTML (variantes, merci, légal)

**Files:**
- Create: `landing/app/templates/base.html`, `landing/app/templates/landing.html`, `landing/app/templates/merci.html`, `landing/app/templates/legal.html`, `landing/app/main.py`
- Modify: `landing/app/routes.py` (ajout des routes GET), `landing/app/factory.py` (globals Jinja)
- Test: `landing/tests/test_pages.py`

**Interfaces:**
- Consumes: `VARIANTS`, `commun`, `legal.PAGES` (T4), `offer.places_restantes` (T4), `brand.identity.NAME / DOMAIN_SUFFIX / TAGLINE`, `brand.export.SUFFIX_RATIO`, `brand.logo.logo_svg` (existants), fixtures T6.
- Produces: routes GET `/`, `/laveur-vitres`, `/infirmier`, `/services-domicile`, `/merci`, `/mentions-legales`, `/confidentialite`. Le formulaire porte `data-lead-form`, chaque erreur a `data-error-for="<champ>"`, le message global `data-form-status`, le formulaire porte `data-network-error`. `app.main:app` pour uvicorn.

- [ ] **Step 1: Écrire le test qui échoue**

`landing/tests/test_pages.py` :

```python
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
```

- [ ] **Step 2: Lancer, vérifier l'échec**

Run: `uv run pytest tests/test_pages.py -q`
Expected: FAIL (404 sur `/` puisque aucune route GET n'existe)

- [ ] **Step 3: Ajouter les globals Jinja dans `factory.py`**

Dans `create_app`, juste après la création de `templates`, ajouter :

```python
    templates.env.globals.update(
        name=NAME,
        domain_suffix=DOMAIN_SUFFIX,
        tagline=TAGLINE,
        logo_svg=logo_svg(),
        commun=commun,
        contact_email=settings.contact_email,
    )
```

et les imports en tête de `factory.py` :

```python
from app.content import commun
from brand.identity import DOMAIN_SUFFIX, NAME, TAGLINE
from brand.logo import logo_svg
```

- [ ] **Step 4: Ajouter les routes GET dans `routes.py`**

Ajouter les imports :

```python
from fastapi.responses import HTMLResponse

from app.content import VARIANTS, legal
from app.content.models import Variant
from app.offer import places_restantes
```

Dans `build_router`, avant `return router`, ajouter :

```python
    def variant_page(variant: Variant):
        def endpoint(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(
                request,
                "landing.html",
                {
                    "variant": variant,
                    "places": places_restantes(repository.count()),
                    "utm_source": request.query_params.get("utm_source", ""),
                    "utm_campaign": request.query_params.get("utm_campaign", ""),
                },
            )

        return endpoint

    for variant in VARIANTS.values():
        router.add_api_route(variant.path, variant_page(variant), methods=["GET"], response_class=HTMLResponse)

    @router.get("/merci", response_class=HTMLResponse)
    def thank_you(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "merci.html", {"calcom_url": settings.calcom_url})

    def legal_page(title: str, paragraphs: tuple[str, ...]):
        def endpoint(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(request, "legal.html", {"title": title, "paragraphs": paragraphs})

        return endpoint

    for path, (title, paragraphs) in legal.PAGES.items():
        router.add_api_route(path, legal_page(title, paragraphs), methods=["GET"], response_class=HTMLResponse)
```

- [ ] **Step 5: Écrire les templates**

`landing/app/templates/base.html` :

```html
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ name }}{{ domain_suffix }} · {{ tagline }}</title>
  <meta name="description" content="{% block description %}{{ tagline }}{% endblock %}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{{ name }}{{ domain_suffix }} · {{ tagline }}">
  <meta property="og:description" content="{{ self.description() }}">
  <meta property="og:image" content="{{ request.base_url }}static/brand/og-image.png">
  <link rel="icon" href="/static/brand/favicon.ico" sizes="48x48">
  <link rel="icon" href="/static/brand/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/static/brand/apple-touch-icon.png">
  <link rel="preload" href="/static/fonts/manrope.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/static/fonts/fraunces.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/static/css/app.css">
</head>
<body class="bg-fond font-sans text-texte antialiased">
  <header class="mx-auto flex max-w-5xl items-center px-4 py-5">
    <a href="/" class="flex items-center gap-3" aria-label="{{ name }}{{ domain_suffix }}, accueil">
      <span class="logo block size-10" aria-hidden="true">{{ logo_svg | safe }}</span>
      <span class="text-2xl font-extrabold tracking-tight">{{ name }}<span class="text-[0.5em] font-bold">{{ domain_suffix }}</span></span>
    </a>
  </header>
  <main>{% block main %}{% endblock %}</main>
  <footer class="mx-auto max-w-5xl px-4 py-10 text-sm text-texte/70">
    <p>{{ name }}{{ domain_suffix }} · {{ tagline }}</p>
    <nav class="mt-3 flex flex-wrap gap-x-5 gap-y-2">
      <a class="underline" href="/mentions-legales">Mentions légales</a>
      <a class="underline" href="/confidentialite">Confidentialité</a>
      <a class="underline" href="mailto:{{ contact_email }}?subject=Désinscription">Se désinscrire</a>
    </nav>
  </footer>
  {% block scripts %}{% endblock %}
</body>
</html>
```

`landing/app/templates/landing.html` :

```html
{% extends "base.html" %}
{% block description %}{{ variant.sous_titre }}{% endblock %}
{% block main %}
<section class="mx-auto max-w-5xl px-4 pt-6 pb-16">
  <h1 class="font-douleur text-4xl leading-tight font-semibold sm:text-6xl">{{ variant.h1 }}</h1>
  <p class="mt-5 max-w-2xl text-lg sm:text-xl">{{ variant.sous_titre }}</p>
  <a href="#formulaire" class="mt-8 inline-block rounded-2xl bg-accent px-7 py-4 text-lg font-extrabold text-texte">{{ commun.CTA }}</a>
  <p class="mt-3 font-bold">{{ commun.SOUS_CTA }}</p>
</section>

<section class="bg-principale/5 py-16">
  <div class="mx-auto max-w-5xl px-4">
    <h2 class="text-3xl font-bold text-principale">{{ commun.UTILITE_TITRE }}</h2>
    <ul class="mt-8 grid gap-5 sm:grid-cols-3">
      {% for pain in variant.douleurs %}
      <li class="rounded-2xl bg-fond p-6 ring-1 ring-texte/10">
        <p class="text-lg font-bold">{{ pain.probleme }}</p>
        <p class="mt-3">{{ pain.solution }}</p>
      </li>
      {% endfor %}
    </ul>
  </div>
</section>

{% for title, items in [(commun.FAISABILITE_TITRE, commun.FAISABILITE), (commun.MORALE_TITRE, commun.MORALE)] %}
<section class="mx-auto max-w-5xl px-4 py-16">
  <h2 class="text-3xl font-bold text-principale">{{ title }}</h2>
  <ul class="mt-8 grid gap-6 sm:grid-cols-3">
    {% for item_title, item_text in items %}
    <li><p class="text-lg font-bold">{{ item_title }}</p><p class="mt-2">{{ item_text }}</p></li>
    {% endfor %}
  </ul>
</section>
{% endfor %}

<section class="bg-principale/5 py-16">
  <div class="mx-auto max-w-5xl px-4">
    <h2 class="text-3xl font-bold text-principale">{{ commun.OPPORTUNITE_TITRE }}</h2>
    <p class="mt-6 flex flex-wrap items-baseline gap-x-4 gap-y-2">
      <s class="text-xl text-texte/60">{{ commun.PRIX_NORMAL }}</s>
      <span class="text-4xl font-extrabold text-accent">{{ commun.PRIX_EARLY }}</span>
    </p>
    <p class="mt-3 text-lg font-bold">{{ commun.ECONOMIE }}</p>
    <p class="mt-6 text-xl font-bold text-accent">{{ commun.compteur(places) }}</p>
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
      <input type="checkbox" name="accepte_appel" class="mt-1 size-5 accent-principale">
      <span>{{ commun.ACCEPTE_APPEL }}</span>
    </label>
    <div>
      <label class="flex items-start gap-3">
        <input type="checkbox" name="consentement_rgpd" required class="mt-1 size-5 accent-principale">
        <span>{{ commun.CONSENTEMENT }} <a class="underline" href="/confidentialite">Politique de confidentialité</a></span>
      </label>
      <span data-error-for="consentement_rgpd" class="mt-1 block font-bold"></span>
    </div>

    <div class="honeypot" aria-hidden="true">
      <label>Site web <input type="text" name="website" tabindex="-1" autocomplete="off"></label>
    </div>

    <button type="submit" class="w-full rounded-2xl bg-accent px-7 py-4 text-lg font-extrabold text-texte disabled:opacity-60">{{ commun.CTA }}</button>
    <p data-form-status role="status" class="font-bold"></p>
  </form>
</section>
{% endblock %}
{% block scripts %}<script src="/static/js/lead-form.js" defer></script>{% endblock %}
```

`landing/app/templates/merci.html` :

```html
{% extends "base.html" %}
{% block main %}
<section class="mx-auto max-w-2xl px-4 py-20">
  <h1 class="font-douleur text-5xl font-semibold">{{ commun.MERCI_TITRE }}</h1>
  <p class="mt-6 text-xl font-bold">{{ commun.MERCI_TEXTE }}</p>
  <p class="mt-4 text-lg">{{ commun.MERCI_APPEL }}</p>
  <a href="{{ calcom_url }}" class="mt-8 inline-block rounded-2xl bg-accent px-7 py-4 text-lg font-extrabold text-texte">{{ commun.MERCI_LIEN }}</a>
</section>
{% endblock %}
```

`landing/app/templates/legal.html` :

```html
{% extends "base.html" %}
{% block main %}
<section class="mx-auto max-w-2xl px-4 py-16">
  <h1 class="text-4xl font-extrabold text-principale">{{ title }}</h1>
  {% for paragraph in paragraphs %}<p class="mt-5 text-lg">{{ paragraph }}</p>{% endfor %}
</section>
{% endblock %}
```

Note : `<script src=... defer>` n'est pas un script inline ; le test `test_templates_have_no_inline_script` cherche `<script>` sans attribut. Dans `base.html`, la classe du suffixe est `text-[0.5em]` (= `SUFFIX_RATIO`), vérifiée par `test_wordmark_suffix_class_matches_brand_ratio`.

`landing/app/main.py` :

```python
from pathlib import Path

from app.factory import build_repository, create_app
from app.settings import load_settings

settings = load_settings(Path(__file__).parent.parent / "secret.toml")
app = create_app(settings, build_repository(settings))
```

- [ ] **Step 6: Lancer, vérifier le vert**

Run: `uv run pytest -q`
Expected: PASS (y compris `test_copy_uses_vouvoiement_and_no_em_dash` qui scanne maintenant les templates)

- [ ] **Step 7: Commit**

```bash
git add landing/app landing/tests/test_pages.py
git commit -m "feat(landing): variant, thank-you and legal pages"
```

---

### Task 8: Front (CSS Tailwind, script du formulaire, animation du logo) et vérification navigateur

**Files:**
- Create: `landing/app/static_src/input.css`, `landing/static/js/lead-form.js`, `landing/README.md`
- Modify: `CLAUDE.md` (section Commandes)

**Interfaces:**
- Consumes: `app/static_src/theme.css` (T5), attributs `data-lead-form`, `data-error-for`, `data-form-status`, `data-network-error` (T7), contrat HTTP de `/api/leads` (T6).
- Produces: `static/css/app.css` (généré), comportement du formulaire.

Pas de test automatisé côté JS : le script ne contient aucune logique métier (le serveur renvoie les messages déjà rédigés). La vérification est manuelle (CLAUDE.md : pas d'E2E en V1).

- [ ] **Step 1: Écrire la feuille Tailwind**

`landing/app/static_src/input.css` :

```css
@import "tailwindcss";
@import "./theme.css";
@source "../templates";

@font-face {
  font-family: "Manrope";
  src: url("/static/fonts/manrope.woff2") format("woff2");
  font-weight: 400 800;
  font-display: swap;
}

@font-face {
  font-family: "Fraunces";
  src: url("/static/fonts/fraunces.woff2") format("woff2");
  font-weight: 600;
  font-display: swap;
}

/* La route du logo se trace au chargement : seule animation de la page (cf. spec). */
@keyframes trace-route {
  from { stroke-dashoffset: 180; }
}

.logo path {
  animation: trace-route 1.2s ease-out both;
}

@media (prefers-reduced-motion: reduce) {
  .logo path { animation: none; }
}

/* Honeypot hors écran plutôt que display:none, que certains robots savent ignorer. */
.honeypot {
  position: absolute;
  left: -10000px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}
```

- [ ] **Step 2: Compiler le CSS**

Run (depuis `landing/`) :

```bash
TAILWINDCSS_VERSION=v4.1.11 uv run tailwindcss -i app/static_src/input.css -o static/css/app.css --minify
```

Expected: `static/css/app.css` créé, contient `--color-accent` et aucune couleur Tailwind par défaut :

```bash
grep -c -- "--color-red-500" static/css/app.css
```

Expected: `0` (la palette par défaut de Tailwind est bien effacée : pas de 5e teinte possible). Si le téléchargement de `v4.1.11` échoue, prendre la dernière `v4.1.x` listée sur https://github.com/tailwindlabs/tailwindcss/releases et reporter la version dans `README.md` et `CLAUDE.md`.

- [ ] **Step 3: Écrire le script du formulaire**

`landing/static/js/lead-form.js` :

```js
const form = document.querySelector("[data-lead-form]");

if (form) {
  const button = form.querySelector("button[type=submit]");
  const status = form.querySelector("[data-form-status]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    status.textContent = "";
    form.querySelectorAll("[data-error-for]").forEach((element) => {
      element.textContent = "";
    });

    const data = Object.fromEntries(new FormData(form));
    data.accepte_appel = form.elements.accepte_appel.checked;
    data.consentement_rgpd = form.elements.consentement_rgpd.checked;
    for (const key of ["utm_source", "utm_campaign"]) {
      if (!data[key]) delete data[key];
    }

    try {
      const response = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const body = await response.json();
      if (response.status === 201) {
        window.location.assign(body.redirect);
        return;
      }
      for (const [field, message] of Object.entries(body.errors ?? {})) {
        const target = form.querySelector(`[data-error-for="${field}"]`);
        if (target) target.textContent = message;
      }
      if (body.message) status.textContent = body.message;
    } catch {
      status.textContent = form.dataset.networkError;
    } finally {
      button.disabled = false;
    }
  });
}
```

- [ ] **Step 4: Documenter les commandes**

`landing/README.md` :

```markdown
# Landing Bouclé.tech

Tout se lance depuis `landing/` avec uv.

1. `cp secret.toml.example secret.toml` (phase 1 : `LEAD_STORE = "memory"`, les leads sont perdus au redémarrage)
2. `uv run python -m brand.export` : logos, favicons, og-image, GIF, polices woff2, tokens Tailwind
3. `TAILWINDCSS_VERSION=v4.1.11 uv run tailwindcss -i app/static_src/input.css -o static/css/app.css --minify`
4. `uv run uvicorn app.main:app --reload` puis http://127.0.0.1:8000

Tests : `uv run pytest -q`
```

Ajouter à la fin de `CLAUDE.md` :

```markdown
## Commandes landing (depuis `landing/`)

- Tests : `uv run pytest -q`
- Assets de marque + polices + tokens : `uv run python -m brand.export`
- CSS : `TAILWINDCSS_VERSION=v4.1.11 uv run tailwindcss -i app/static_src/input.css -o static/css/app.css --minify`
- Serveur : `uv run uvicorn app.main:app --reload`
```

- [ ] **Step 5: Vérification navigateur (skill `run`), desktop puis mobile (375 px)**

Lancer le serveur (`cp secret.toml.example secret.toml` si absent, puis `uv run uvicorn app.main:app --reload`) et vérifier, sur chacune des 4 variantes :

- [ ] H1 en Fraunces, reste en Manrope, CTA ambre lisible, aucune couleur hors palette.
- [ ] La route du logo se trace au chargement ; avec « réduire les animations » activé côté OS, pas d'animation.
- [ ] `/laveur-vitres` et `/infirmier` : métier pré-sélectionné ; `/` et `/services-domicile` : « Choisissez ».
- [ ] Envoi vide : messages sous chaque champ requis, rien n'est stocké.
- [ ] Envoi valide : redirection vers `/merci` (« C'est bouclé. », lien Cal.com) ; retour sur `/` : compteur passé de 10 à 9.
- [ ] Même email renvoyé (avec majuscules) : « Vous êtes déjà sur la liste. À très vite ! ».
- [ ] Double clic rapide sur le bouton : un seul lead créé (compteur -1), aucun message d'erreur incohérent (Review Focus 5).
- [ ] Serveur coupé puis envoi : message d'erreur avec l'email de contact, pas de faux succès.
- [ ] Mobile 375 px : pas de défilement horizontal, cibles tactiles ≥ 44 px, texte ≥ 16 px.
- [ ] Liens pied de page : mentions légales, confidentialité, « Se désinscrire » ouvre le client mail.

- [ ] **Step 6: Lancer toute la suite**

Run: `uv run pytest -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add landing/app/static_src/input.css landing/static/js/lead-form.js landing/README.md CLAUDE.md
git commit -m "feat(landing): Tailwind styles, lead form script and logo animation"
```
