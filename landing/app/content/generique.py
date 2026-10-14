from datetime import time
from decimal import Decimal

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="generique",
    path="/",
    metier_prefill=None,
    taxe="HT",
    h1="Un imprévu à 7h, et toute la journée déraille ?",
    sous_titre="Bouclé recalcule votre tournée et prévient vos clients par SMS. Vous, vous conduisez.",
    douleurs=(
        Pain(
            "Un client annule, un autre ajoute un passage.",
            "Votre tournée se réorganise en un geste. Les clients concernés reçoivent leur nouvel horaire par SMS.",
            "calendar-check",
        ),
        Pain(
            "Des kilomètres en trop, sans s'en rendre compte.",
            "Bouclé ordonne vos arrêts et chiffre le coût de chaque journée : carburant, temps, rentabilité.",
            "map-pin",
        ),
        Pain(
            "Le planning de la semaine tient dans votre tête.",
            "Il tient sur une page : imprimable chaque matin, partageable avec vos collègues.",
            "printer",
        ),
    ),
    demo=DemoScenario(
        debut=time(8, 0),
        positions=((30, 160), (90, 70), (160, 140), (230, 60), (290, 130)),
        incident=Incident(kind="ajout", position=2, label="Un client ajoute un passage", icon="plus-circle"),
        ajout_xy=(140, 40),
        sms="Bonjour, votre passage est décalé à {heure}. Bouclé.tech",
    ),
    rentabilite=Hypotheses(km_par_semaine=30, heures_admin_par_mois=2, no_show_par_mois=1, valeur_passage=Decimal("40")),
)
