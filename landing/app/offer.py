from decimal import Decimal

PRIX_HT = Decimal("49")
TAUX_TVA = Decimal("0.20")
PRIX_EARLY_ACCESS_HT = PRIX_HT / 2
# Valeur mock : N sera fixé par l'arbitrage marketing (cf. spec, section Opportunité).
PLACES_EARLY_ACCESS = 10


def format_euros(montant: Decimal) -> str:
    if montant == montant.to_integral_value():
        return str(int(montant))
    return f"{montant:.2f}".replace(".", ",")


def avec_tva(montant_ht: Decimal) -> Decimal:
    return (montant_ht * (1 + TAUX_TVA)).quantize(Decimal("0.01"))


def economie_annuelle_ht() -> Decimal:
    return (PRIX_HT - PRIX_EARLY_ACCESS_HT) * 12


def est_en_liste_attente(rang_inscription: int) -> bool:
    return rang_inscription > PLACES_EARLY_ACCESS


def places_restantes(inscrits: int) -> int:
    return max(PLACES_EARLY_ACCESS - inscrits, 0)
