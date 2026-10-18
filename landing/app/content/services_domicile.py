from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="services-domicile",
    path="/services-domicile",
    metier_prefill=None,
    taxe="HT",
    clientele="clients",
    h1="Plusieurs demandes à caser, et votre semaine reste sous contrôle.",
    sous_titre=(
        "Bouclé.tech trouve le bon ordre de passage et prévient vos clients par SMS. "
        "Vous arrivez à l'heure, sereinement."
    ),
    douleurs=(
        Pain(
            "Des demandes qui arrivent au fil de la journée.",
            "Vous les ajoutez en quelques secondes, Bouclé.tech leur trouve une place dans la semaine.",
            "plus-circle",
        ),
        Pain(
            "Les pics de saison (taille, ramonage, entretien).",
            "Bouclé.tech répartit les passages sur plusieurs semaines, sans oublier personne.",
            "calendar-check",
        ),
        Pain(
            "Plusieurs intervenants à coordonner.",
            "Chacun reçoit sa tournée, vous gardez la vue d'ensemble.",
            "map-pin",
        ),
    ),
    demo=DemoScenario(
        debut=time(13, 30),
        positions=((30, 120), (100, 50), (170, 130), (240, 60), (295, 140)),
        incident=Incident(kind="ajout", position=1, label="Demande urgente", icon="lightning"),
        ajout_xy=(45, 60),
        sms="Bonjour, votre passage est décalé à {heure}. Bouclé.tech",
    ),
    rentabilite=Hypotheses(km_par_semaine=25, heures_par_semaine=2, no_show_par_mois=1),
)
