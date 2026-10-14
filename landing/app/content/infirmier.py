from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident

# Aucune donnée ni mention de santé : on parle de tournée, d'horaires et de trajets (cf. spec, HDS).
VARIANT = Variant(
    slug="infirmier",
    path="/infirmier",
    metier_prefill="infirmier",
    taxe="TTC",
    h1="Un passage ajouté en dernière minute, et toute la tournée glisse ?",
    sous_titre=(
        "Bouclé réorganise votre tournée en respectant vos horaires fixes, "
        "et prévient vos patients de l'heure de passage."
    ),
    douleurs=(
        Pain(
            "Des passages à heure fixe à tenir coûte que coûte.",
            "Vous les verrouillez : Bouclé organise le reste de la tournée autour.",
            "clock-countdown",
        ),
        Pain(
            "Un patient absent ou un remplacement imprévu.",
            "La tournée se recalcule, les patients suivants reçoivent leur nouvel horaire par SMS.",
            "user-minus",
        ),
        Pain(
            "Les kilomètres du cabinet, mal répartis.",
            "Une vue claire des trajets de la journée, imprimable, partageable avec vos collègues ou votre remplaçante.",
            "map-pin",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 30),
        positions=((30, 60), (90, 140), (155, 70), (220, 150), (290, 80)),
        incident=Incident(kind="retrait", position=2, label="Patient absent", icon="user-minus"),
        sms="Bonjour, mon passage chez vous est avancé à {heure}. Bouclé.tech",
    ),
)
