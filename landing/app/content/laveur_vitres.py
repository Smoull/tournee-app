from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="laveur-vitres",
    path="/laveur-vitres",
    metier_prefill="laveur-vitres",
    taxe="HT",
    clientele="clients",
    h1="Une annulation en début de journée, et votre tournée reste sous contrôle.",
    sous_titre=(
        "Bouclé.tech recalcule la tournée et prévient vos clients par SMS. "
        "Votre matinée reste productive."
    ),
    douleurs=(
        Pain(
            "La météo qui décale toute la journée.",
            "Vous reportez en un geste, Bouclé.tech repropose les créneaux et prévient chaque client.",
            "cloud-rain",
        ),
        Pain(
            "Des passages réguliers à ne pas oublier.",
            "Les clients récurrents reviennent automatiquement dans votre planning, au bon rythme.",
            "calendar-check",
        ),
        Pain(
            "Un client absent, un déplacement perdu.",
            "La veille, un SMS confirme le passage. Le client absent se signale à l'avance.",
            "chat-text",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 0),
        positions=((30, 150), (85, 60), (150, 120), (215, 50), (285, 110)),
        incident=Incident(kind="retrait", position=0, label="Annulation à 7h", icon="x-circle"),
        sms="Bonjour, nous pouvons passer plus tôt : {heure}. Bouclé.tech",
    ),
    rentabilite=Hypotheses(heures_par_semaine=2),
)
