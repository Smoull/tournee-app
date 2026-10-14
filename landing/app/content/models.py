from dataclasses import dataclass
from typing import Literal

from app.demo.scenario import DemoScenario
from app.rentabilite import Hypotheses


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
    taxe: Literal["HT", "TTC"]
    h1: str
    sous_titre: str
    douleurs: tuple[Pain, Pain, Pain]
    demo: DemoScenario
    rentabilite: Hypotheses
