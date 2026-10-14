from app.offer import PLACES_EARLY_ACCESS, PRIX_EARLY_ACCESS_HT, PRIX_HT, economie_annuelle_ht

CTA = "Je réserve ma place"
SOUS_CTA = f"{PRIX_EARLY_ACCESS_HT} € HT/mois à vie pour les {PLACES_EARLY_ACCESS} premiers."

UTILITE_TITRE = "Ce que Bouclé change dans votre journée"

FAISABILITE_TITRE = "On configure tout pour vous"
FAISABILITE = (
    ("Prise en main en 5 minutes.", "On importe vos clients avec vous, au téléphone si besoin."),
    ("Votre tournée sur papier.", "Un PDF clair, imprimable chaque matin."),
    ("Vous gardez la main.", "Bouclé propose, vous validez ou vous modifiez. Toujours."),
)

MORALE_TITRE = "Vos données restent les vôtres"
MORALE = (
    ("Hébergées en France.", "Jamais revendues, jamais partagées."),
    ("Vos clients respectés.", "Prévenus avant, jamais surpris par un retard."),
    ("Du temps rendu.", "Moins de trajets et de coups de fil, plus de soirées pour vous et vos proches."),
)

OPPORTUNITE_TITRE = "Early access : le prix des premiers, à vie"
PRIX_NORMAL = f"{PRIX_HT} € HT/mois"
PRIX_EARLY = f"{PRIX_EARLY_ACCESS_HT} € HT/mois à vie"
ECONOMIE = f"-{PRIX_HT - PRIX_EARLY_ACCESS_HT} € HT/mois à vie, soit {economie_annuelle_ht()} € HT économisés chaque année."
ATTENTE = (
    f"Après les {PLACES_EARLY_ACCESS} premières places, le tarif passe à {PRIX_HT} € HT/mois. "
    "Sans engagement : vous réservez votre place, vous ne payez rien aujourd'hui."
)


def compteur(places: int) -> str:
    if places == 0:
        return "Toutes les places early access sont prises : inscrivez-vous pour la liste d'attente."
    if places == 1:
        return "Plus qu'une place au tarif early access."
    return f"Plus que {places} places au tarif early access."


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
ACCEPTE_APPEL = "J'accepte un appel de 15 minutes pour parler de ma tournée."
CONSENTEMENT = "J'accepte que Bouclé.tech utilise ces informations pour me recontacter au sujet de l'early access."

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
MERCI_TEXTE = f"Votre place early access est réservée : {PRIX_EARLY_ACCESS_HT} € HT/mois à vie."
MERCI_APPEL = "On vous recontacte très vite. Pour aller plus vite, réservez un appel de 15 minutes."
MERCI_LIEN = "Choisir un créneau"
