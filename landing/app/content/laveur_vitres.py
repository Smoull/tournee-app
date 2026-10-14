from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident

VARIANT = Variant(
    slug="laveur-vitres",
    path="/laveur-vitres",
    metier_prefill="laveur-vitres",
    h1="Un client annule à 7h ?",
    sous_titre="Votre tournée se recalcule, vos clients sont prévenus par SMS. Vous gardez votre matinée.",
    douleurs=(
        Pain(
            "La pluie décale toute la journée.",
            "Reportez en un geste : Bouclé repropose les créneaux et prévient chaque client.",
            "cloud-rain",
        ),
        Pain(
            "Les passages tous les 2 mois, il faut s'en souvenir.",
            "Les clients récurrents reviennent tout seuls dans votre planning, au bon rythme.",
            "calendar-check",
        ),
        Pain(
            "Porte fermée, client absent, trajet pour rien.",
            "La veille, un SMS confirme le passage. Le client absent se signale avant, pas après.",
            "chat-text",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 0),
        positions=((30, 150), (85, 60), (150, 120), (215, 50), (285, 110)),
        incident=Incident(kind="retrait", position=0, label="Annulation à 7h", icon="x-circle"),
        sms="Bonjour, nous pouvons passer plus tôt : {heure}. Bouclé.tech",
    ),
)
