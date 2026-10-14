from decimal import Decimal

PRIX_HT = Decimal("49")
# Infirmiers exonérés de TVA : prix TTC arrondi plutôt que 49 € HT x 1,2 = 58,80 €.
PRIX_TTC = Decimal("59")
REMISE_ACCES_ANTICIPE = Decimal("0.5")
# Valeur mock : N sera fixé par l'arbitrage marketing (cf. spec, section Opportunité).
PLACES_EARLY_ACCESS = 10


def format_euros(montant: Decimal) -> str:
    if montant == montant.to_integral_value():
        return str(int(montant))
    return f"{montant:.2f}".replace(".", ",")


def prix_acces_anticipe(prix: Decimal) -> Decimal:
    return prix * (1 - REMISE_ACCES_ANTICIPE)


def economie_annuelle(prix: Decimal) -> Decimal:
    return (prix - prix_acces_anticipe(prix)) * 12


PRIX_EARLY_ACCESS_HT = prix_acces_anticipe(PRIX_HT)


def economie_annuelle_ht() -> Decimal:
    return economie_annuelle(PRIX_HT)


def est_en_liste_attente(rang_inscription: int) -> bool:
    return rang_inscription > PLACES_EARLY_ACCESS


def places_restantes(inscrits: int) -> int:
    return max(PLACES_EARLY_ACCESS - inscrits, 0)
