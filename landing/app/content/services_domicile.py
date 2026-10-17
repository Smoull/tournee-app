from datetime import time
from decimal import Decimal

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="services-domicile",
    path="/services-domicile",
    metier_prefill=None,
    taxe="HT",
    h1="Trois clients à caser, un seul après-midi, et le téléphone qui sonne encore.",
    sous_titre=(
        "Bouclé.tech trouve le bon ordre de passage et prévient vos clients par SMS. "
        "Vous arrivez à l'heure, sans courir entre deux portails."
    ),
    douleurs=(
        Pain(
            "Les demandes arrivent en vrac, au téléphone, pendant que vous avez les mains dans la haie.",
            "Ajoutez-les en quelques secondes : Bouclé.tech leur trouve une place dans la semaine. "
            "Fini les post-it sur le tableau de bord.",
            "plus-circle",
        ),
        Pain(
            "En saison (taille, ramonage, entretien), tout le monde veut passer « avant la fin du mois ».",
            "Bouclé.tech répartit les passages sur plusieurs semaines, sans oublier personne. "
            "Pas même celui qui a appelé trois fois.",
            "calendar-check",
        ),
        Pain(
            "Trois intervenants, deux camionnettes, une seule question : qui va où ?",
            "Chacun reçoit sa tournée, vous gardez la vue d'ensemble. Fini le briefing à 7h sur le parking.",
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
    rentabilite=Hypotheses(km_par_semaine=25, heures_admin_par_mois=2, no_show_par_mois=1, valeur_passage=Decimal("35")),
)
