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
    h1="7h05, un client annule. 7h06, votre journée entière est à refaire.",
    sous_titre=(
        "Bouclé.tech recalcule la tournée et prévient vos clients par SMS. "
        "Vous conduisez, le téléphone reste dans la poche."
    ),
    douleurs=(
        Pain(
            "Un client annule, un autre veut passer « juste avant midi, si possible ».",
            "Un geste, la tournée se réorganise. Les clients concernés reçoivent leur nouvel horaire par SMS, "
            "sans que vous décrochiez.",
            "calendar-check",
        ),
        Pain(
            "Le soir, le compteur affiche 40 km de plus que prévu. Personne ne sait où ils sont passés.",
            "Bouclé.tech ordonne vos arrêts et chiffre chaque journée : carburant, temps, rentabilité. "
            "Les kilomètres fantômes disparaissent.",
            "map-pin",
        ),
        Pain(
            "Le planning de la semaine tient dans votre tête. Jusqu'au jour où un client passe à la trappe.",
            "Il tient sur une page, imprimable chaque matin et partageable avec vos collègues. "
            "Votre mémoire peut souffler.",
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
