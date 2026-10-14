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
