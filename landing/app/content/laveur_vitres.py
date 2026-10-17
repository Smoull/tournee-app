from datetime import time
from decimal import Decimal

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

VARIANT = Variant(
    slug="laveur-vitres",
    path="/laveur-vitres",
    metier_prefill="laveur-vitres",
    taxe="HT",
    h1="6h58, un client annule. L'échelle est déjà sur le camion.",
    sous_titre=(
        "Bouclé.tech recalcule la tournée et prévient vos clients par SMS. "
        "Vous gardez votre matinée, et votre raclette ne chôme pas."
    ),
    douleurs=(
        Pain(
            "Il pleut. Encore. Et toute la journée est à décaler.",
            "Reportez en un geste : Bouclé.tech repropose les créneaux et prévient chaque client. "
            "Vous, vous regardez la pluie avec un café.",
            "cloud-rain",
        ),
        Pain(
            "Le passage tous les 2 mois chez la boulangerie : noté où, déjà ?",
            "Les clients récurrents reviennent tout seuls dans votre planning, au bon rythme. "
            "Le carnet à spirale peut prendre sa retraite.",
            "calendar-check",
        ),
        Pain(
            "Porte fermée, volets clos, 25 minutes de route pour rien.",
            "La veille, un SMS confirme le passage. Le client absent se signale avant, "
            "pas quand vous êtes déjà sur le trottoir.",
            "chat-text",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 0),
        positions=((30, 150), (85, 60), (150, 120), (215, 50), (285, 110)),
        incident=Incident(kind="retrait", position=0, label="Annulation à 7h", icon="x-circle"),
        sms="Bonjour, nous pouvons passer plus tôt : {heure}. Bouclé.tech",
    ),
    rentabilite=Hypotheses(km_par_semaine=30, heures_admin_par_mois=2, no_show_par_mois=2, valeur_passage=Decimal("45")),
)
