PRIX_HT = 29
PRIX_EARLY_ACCESS_HT = 19
# Valeur mock : N sera fixé par l'arbitrage marketing (cf. spec, section Opportunité).
PLACES_EARLY_ACCESS = 10


def economie_annuelle_ht() -> int:
    return (PRIX_HT - PRIX_EARLY_ACCESS_HT) * 12


def est_en_liste_attente(rang_inscription: int) -> bool:
    return rang_inscription > PLACES_EARLY_ACCESS


def places_restantes(inscrits: int) -> int:
    return max(PLACES_EARLY_ACCESS - inscrits, 0)
