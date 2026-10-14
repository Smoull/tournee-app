from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident

VARIANT = Variant(
    slug="services-domicile",
    path="/services-domicile",
    metier_prefill=None,
    taxe="HT",
    h1="Trois clients à caser, un seul après-midi ?",
    sous_titre="Bouclé trouve le bon ordre de passage et prévient vos clients par SMS. Vous arrivez à l'heure, sans courir.",
    douleurs=(
        Pain(
            "Les demandes arrivent en vrac, au téléphone.",
            "Ajoutez-les en quelques secondes : Bouclé leur trouve une place dans la semaine.",
            "plus-circle",
        ),
        Pain(
            "Les pics de saison (taille, ramonage, entretien) débordent.",
            "Bouclé répartit les passages sur plusieurs semaines, sans oublier personne.",
            "calendar-check",
        ),
        Pain(
            "Plusieurs intervenants, qui va où ?",
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
)
