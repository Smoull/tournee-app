from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="generique",
    path="/",
    metier_prefill=None,
    taxe="HT",
    clientele="clients",
    h1="Un imprévu dans la journée et votre tournée reste sous contrôle.",
    sous_titre=(
        "Bouclé.tech recalcule la tournée et prévient vos clients par SMS. "
        "Vous restez concentré sur la route."
    ),
    douleurs=(
        Pain(
            "Un client annule, un autre demande un passage.",
            "La tournée se réorganise en un geste et les clients concernés "
            "reçoivent leur nouvel horaire par SMS.",
            "calendar-check",
        ),
        Pain(
            "Des kilomètres en trop, difficiles à repérer.",
            "Bouclé.tech ordonne vos arrêts et chiffre chaque journée : carburant, temps, rentabilité.",
            "map-pin",
        ),
        Pain(
            "Un planning qui ne repose que sur votre mémoire.",
            "Il tient sur une page, imprimable chaque matin et partageable avec vos collègues.",
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
    rentabilite=Hypotheses(heures_par_semaine=2),
)
