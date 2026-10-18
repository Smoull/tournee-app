from dataclasses import dataclass
from typing import Literal

from app.rentabilite import Hypotheses, gain_temps_par_mois
from app.offer import PLACES_EARLY_ACCESS, PRIX_HT, PRIX_TTC, economie_annuelle, format_euros, prix_acces_anticipe

Taxe = Literal["HT", "TTC"]

REJOUER = "Rejouer la démo"

UTILITE_TITRE = "Ce que Bouclé.tech change dans votre journée"

RENTABILITE_TITRE = "Rentable dès le premier mois"
RENTABILITE_GAIN = "gagnés par mois, rien qu'en temps (calcul théorique)"
RENTABILITE_LIAISON = "pour"
RENTABILITE_ABONNEMENT = "Votre abonnement en accès anticipé"
RENTABILITE_CHUTE = "Rien qu'avec le temps gagné, votre abonnement est remboursé."
RENTABILITE_MENTION = "Calcul théorique sur la base de 25 euros de l'heure, à adapter à votre activité."


def postes_rentabilite(clientele: str) -> tuple[tuple[str, str, str], tuple[str, str, str], tuple[str, str, str]]:
    return (
        ("Économie d'essence", "Le bon ordre de passage évite les kilomètres inutiles.", "gas-pump"),
        ("Gain de temps", "Moins d'appels et de planning à refaire chaque semaine.", "watch"),
        (f"Absences anticipées des {clientele}", "Le SMS envoyé la veille évite les déplacements inutiles.", "calendar-x"),
    )


def montant_gain(hypotheses: Hypotheses) -> str:
    return f"Environ {gain_temps_par_mois(hypotheses)} €"


FAISABILITE_TITRE = "On configure tout pour vous"
SUPPORT_TOURNEE = (
    "Votre tournée sur papier ou dans votre agenda.",
    "Un PDF clair chaque matin, ou directement dans votre agenda numérique.",
    "printer",
)


def faisabilite(support_tournee: tuple[str, str, str]) -> tuple[tuple[str, str, str], ...]:
    return (
        (
            "Prise en main accompagnée par un expert.",
            "On configure le logiciel avec vous.",
            "clock-countdown",
        ),
        support_tournee,
        ("Vous gardez la main.", "Chaque tournée proposée peut être validée ou ajustée en un geste.", "hand-heart"),
    )

MORALE_TITRE = "Vos données restent les vôtres"


CONFORMITE_RGPD = "Leurs données sont traitées dans le respect du RGPD."


def morale(clientele: str, conformite: str) -> tuple[tuple[str, str, str], ...]:
    return (
        ("Hébergées en France.", "Jamais revendues.", "shield-check"),
        (f"Vos {clientele} respectés.", conformite, "chat-text"),
        ("Exportables à tout moment.", "Vous partez quand vous voulez, avec toutes vos données.", "download-simple"),
    )





@dataclass(frozen=True)
class Cadrage:
    hero_cta: str
    sous_cta: str
    titre: str
    intro: str | None
    sans_engagement: str
    prefixe_prix: str | None
    economie_annuelle: bool
    cta: str
    formulaire_titre: str
    formulaire_intro: str


ACCES_ANTICIPE = Cadrage(
    hero_cta="Lancer ma tournée",
    sous_cta=f"{{prix}} pour les {PLACES_EARLY_ACCESS} premiers.",
    titre="Accès anticipé : rien à payer aujourd'hui",
    intro=None,
    sans_engagement="Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui.",
    prefixe_prix=None,
    economie_annuelle=True,
    cta="Je réserve ma place",
    formulaire_titre="Réservez votre place",
    formulaire_intro="30 secondes. Aucun paiement aujourd'hui.",
)

TEST_GRATUIT = Cadrage(
    hero_cta="Devenir testeur",
    sous_cta="Test gratuit, puis {prix} si vous l'adoptez.",
    titre="Testez Bouclé.tech avec nous",
    intro=(
        f"Bouclé.tech est en construction. Nous cherchons {PLACES_EARLY_ACCESS} cabinets "
        "pour le tester et l'améliorer avec nous."
    ),
    sans_engagement="Sans engagement : vous testez gratuitement, puis vous décidez si vous continuez.",
    prefixe_prix="Si vous l'adoptez :",
    economie_annuelle=False,
    cta="Je veux tester",
    formulaire_titre="Devenez testeur",
    formulaire_intro="Aucun paiement, aucune carte bancaire.",
)


@dataclass(frozen=True)
class Offre:
    prix_normal: str
    prix_early: str
    economie_avant: str
    economie_montant: str
    economie_nombre: str
    economie_apres: str
    attente: str


def offre(taxe: Taxe) -> Offre:
    prix = PRIX_HT if taxe == "HT" else PRIX_TTC
    remise = prix - prix_acces_anticipe(prix)
    normal = format_euros(prix)
    early = format_euros(prix_acces_anticipe(prix))
    economie = economie_annuelle(prix)
    return Offre(
        prix_normal=f"{normal} € {taxe}/mois",
        prix_early=f"{early} € {taxe}/mois à vie",
        economie_avant=f"-{format_euros(remise)} € {taxe}/mois à vie, soit ",
        economie_montant=format_euros(economie),
        economie_nombre=format_euros(economie).replace(",", "."),
        economie_apres=f" € {taxe} économisés chaque année.",
        attente=f"Après les {PLACES_EARLY_ACCESS} premières places, le tarif passe à {normal} € {taxe}/mois.",
    )


def compteur(places: int) -> str:
    if places == 0:
        return "Toutes les places en accès anticipé sont prises : inscrivez-vous pour la liste d'attente."
    if places == 1:
        return "Plus qu'une place en accès anticipé."
    return f"Plus que {places} places en accès anticipé."



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
MERCI_TEXTE = "Votre demande est enregistrée. Si vous adoptez Bouclé.tech : -50 % à vie."
MERCI_ATTENTE = (
    "Les places en accès anticipé sont toutes prises : vous êtes sur la liste d'attente. "
    "On vous prévient dès qu'une place se libère."
)
MERCI_APPEL = "On vous recontacte très vite. Pour aller plus vite, réservez un appel de 15 minutes."
MERCI_LIEN = "Choisir un créneau"
