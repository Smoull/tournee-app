from datetime import time

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

# Aucune donnée ni mention de santé : on parle de tournée, d'horaires et de trajets (cf. spec, HDS).
VARIANT = Variant(
    slug="infirmier",
    path="/infirmier",
    metier_prefill="infirmier",
    taxe="TTC",
    clientele="patients",
    h1="Un passage ajouté, et votre tournée reste sous contrôle.",
    sous_titre=(
        "Bouclé.tech réorganise la tournée autour de vos horaires fixes "
        "et prévient vos patients de l'heure de passage."
    ),
    douleurs=(
        Pain(
            "Gestion automatique des passages à heure fixe.",
            "Vous indiquez les passages à heure fixe, Bouclé.tech organise le reste de la tournée.",
            "clock-countdown",
        ),
        Pain(
            "Un patient absent ou un imprévu.",
            "La tournée se recalcule et les patients suivants reçoivent leur nouvel horaire par SMS.",
            "user",
        ),
        Pain(
            "Des trajets optimisés.",
            "Moins d'essence dépensée chaque jour, une vue claire des trajets, facile à partager.",
            "map-pin",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 30),
        positions=((30, 60), (90, 140), (155, 70), (220, 150), (290, 80)),
        incident=Incident(kind="retrait", position=2, label="Patient absent", icon="user-minus"),
        sms="Bonjour, mon passage chez vous est avancé à {heure}. Votre infirmière, Florence.",
    ),
    rentabilite=Hypotheses(km_par_semaine=40, heures_par_semaine=2, no_show_par_mois=2),
    support_tournee=(
        "Un planning partagé avec tout le cabinet.",
        "Un remplacement d'un confrère, un imprévu : mise à jour de l'agenda automatique.",
        "calendar-check",
    ),
    conformite="Leurs données sont traitées dans le respect du RGPD, chez un hébergeur certifié HDS.",
)
