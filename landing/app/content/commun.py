from dataclasses import dataclass
from typing import Literal

from app.rentabilite import Hypotheses
from app.offer import PLACES_EARLY_ACCESS, PRIX_HT, PRIX_TTC, economie_annuelle, format_euros, prix_acces_anticipe

Taxe = Literal["HT", "TTC"]

CTA = "Je réserve ma place"
REJOUER = "Rejouer la démo"

UTILITE_TITRE = "Ce que Bouclé.tech change dans votre journée"

RENTABILITE_TITRE = "Bouclé.tech se rembourse tout seul"
RENTABILITE_POSTES = (("Moins d'essence", "gas-pump"), ("Moins de paperasse", "files"), ("Moins de déplacements pour rien", "door-open"))
RENTABILITE_GAIN = "gagnés par mois (calcul théorique)"
RENTABILITE_ABONNEMENT = "Votre abonnement en accès anticipé"
RENTABILITE_CHUTE = "Rentabilisé dès le premier déplacement pour rien évité."
RENTABILITE_MENTION = (
    "Calcul théorique, à ajuster à votre activité : carburant à 2 euros le litre pour 6,5 litres aux 100 km, "
    "votre heure de travail comptée 30 euros."
)


def lignes_rentabilite(hypotheses: Hypotheses) -> tuple[str, str, str]:
    no_show = hypotheses.no_show_par_mois
    deplacements = "1 déplacement pour rien évité" if no_show == 1 else f"{no_show} déplacements pour rien évités"
    return (
        f"{hypotheses.km_par_semaine} km évités par semaine grâce au bon ordre de passage",
        f"{hypotheses.heures_admin_par_mois} h de coups de fil et de planning en moins par mois",
        f"{deplacements} par mois, grâce au SMS de confirmation la veille",
    )


FAISABILITE_TITRE = "On configure tout pour vous"
FAISABILITE = (
    (
        "Prise en main accompagnée par un expert.",
        "On importe vos clients avec vous, au téléphone. 5 minutes et c'est parti.",
        "clock-countdown",
    ),
    (
        "Votre tournée sur papier ou dans votre agenda.",
        "Un PDF clair chaque matin, ou directement dans votre agenda numérique.",
        "printer",
    ),
    ("Vous gardez la main.", "Bouclé.tech propose, vous validez ou vous modifiez. Toujours.", "hand-heart"),
)

MORALE_TITRE = "Vos données restent les vôtres"
MORALE = (
    ("Hébergées en France.", "Jamais revendues, jamais partagées.", "shield-check"),
    ("Vos clients respectés.", "Prévenus avant, jamais surpris par un retard.", "chat-text"),
    ("Du temps rendu.", "Moins de trajets et de coups de fil, plus de soirées pour vous et vos proches.", "clock-countdown"),
)

OPPORTUNITE_TITRE = "Accès anticipé : le prix des premiers, à vie"


@dataclass(frozen=True)
class Offre:
    sous_cta: str
    prix_normal: str
    prix_early: str
    economie_avant: str
    economie_montant: str
    economie_nombre: str
    economie_apres: str
    attente: str
    mention_taxe: str | None


def offre(taxe: Taxe) -> Offre:
    prix = PRIX_HT if taxe == "HT" else PRIX_TTC
    remise = prix - prix_acces_anticipe(prix)
    normal = format_euros(prix)
    early = format_euros(prix_acces_anticipe(prix))
    economie = economie_annuelle(prix)
    return Offre(
        sous_cta=f"{early} € {taxe}/mois à vie pour les {PLACES_EARLY_ACCESS} premiers.",
        prix_normal=f"{normal} € {taxe}/mois",
        prix_early=f"{early} € {taxe}/mois à vie",
        economie_avant=f"-{format_euros(remise)} € {taxe}/mois à vie, soit ",
        economie_montant=format_euros(economie),
        economie_nombre=format_euros(economie).replace(",", "."),
        economie_apres=f" € {taxe} économisés chaque année.",
        attente=(
            f"Après les {PLACES_EARLY_ACCESS} premières places, le tarif passe à {normal} € {taxe}/mois. "
            "Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui."
        ),
        mention_taxe=None if taxe == "HT" else "Prix TTC : votre activité est exonérée de TVA, vous ne la récupérez pas.",
    )


def compteur(places: int) -> str:
    if places == 0:
        return "Toutes les places en accès anticipé sont prises : inscrivez-vous pour la liste d'attente."
    if places == 1:
        return "Plus qu'une place en accès anticipé."
    return f"Plus que {places} places en accès anticipé."


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
ACCEPTE_APPEL = "Oui, appelez-moi 15 minutes pour parler de ma tournée (facultatif)."
CONSENTEMENT = "J'accepte que Bouclé.tech conserve ces informations pour me prévenir de l'ouverture de l'accès anticipé."

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
MERCI_TEXTE = "Votre place en accès anticipé est réservée : -50 % à vie."
MERCI_ATTENTE = (
    "Les places en accès anticipé sont toutes prises : vous êtes sur la liste d'attente. "
    "On vous prévient dès qu'une place se libère."
)
MERCI_APPEL = "On vous recontacte très vite. Pour aller plus vite, réservez un appel de 15 minutes."
MERCI_LIEN = "Choisir un créneau"
