from dataclasses import dataclass

VALEUR_HEURE = 25
SEMAINES_PAR_MOIS = 4


@dataclass(frozen=True)
class Hypotheses:
    km_par_semaine: int
    heures_par_semaine: int
    no_show_par_mois: int


def gain_temps_par_mois(hypotheses: Hypotheses) -> int:
    return hypotheses.heures_par_semaine * SEMAINES_PAR_MOIS * VALEUR_HEURE
