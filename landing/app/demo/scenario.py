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
