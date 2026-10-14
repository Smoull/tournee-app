from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# 7 L/100 km à 1,85 €/L : carburant seul, sans usure ni assurance (estimation prudente).
COUT_CARBURANT_PAR_KM = Decimal("0.13")
VALEUR_HEURE = Decimal("25")
SEMAINES_PAR_MOIS = Decimal(52) / 12


@dataclass(frozen=True)
class Hypotheses:
    km_par_semaine: int
    heures_admin_par_mois: int
    no_show_par_mois: int
    valeur_passage: Decimal


@dataclass(frozen=True)
class Gains:
    essence: int
    administratif: int
    no_show: int

    @property
    def total(self) -> int:
        return self.essence + self.administratif + self.no_show


def _euros(montant: Decimal) -> int:
    return int(montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def gains(hypotheses: Hypotheses) -> Gains:
    return Gains(
        essence=_euros(hypotheses.km_par_semaine * SEMAINES_PAR_MOIS * COUT_CARBURANT_PAR_KM),
        administratif=_euros(hypotheses.heures_admin_par_mois * VALEUR_HEURE),
        no_show=_euros(hypotheses.no_show_par_mois * hypotheses.valeur_passage),
    )
