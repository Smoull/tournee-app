from datetime import time
from decimal import Decimal

from app.content.models import Pain, Variant
from app.demo.scenario import DemoScenario, Incident
from app.rentabilite import Hypotheses

# Aucune donnée ni mention de santé : on parle de tournée, d'horaires et de trajets (cf. spec, HDS).
VARIANT = Variant(
    slug="infirmier",
    path="/infirmier",
    metier_prefill="infirmier",
    taxe="TTC",
    h1="7h12, le cabinet ajoute un passage. 7h13, toute votre tournée a glissé.",
    sous_titre=(
        "Bouclé.tech recale la tournée autour de vos horaires fixes et prévient vos patients "
        "de l'heure de passage. Vous gardez le volant, il garde le planning."
    ),
    douleurs=(
        Pain(
            "Le passage de 8h pile, celui qu'on ne décale pas, même pour un café.",
            "Vous le verrouillez une fois. Bouclé.tech construit le reste autour, sans discuter.",
            "clock-countdown",
        ),
        Pain(
            "Vous sonnez, personne. Le patient est parti chez sa fille depuis hier.",
            "Un clic, la tournée se recalcule et les suivants reçoivent leur nouvel horaire par SMS. "
            "Fini les dix appels depuis la voiture.",
            "user-minus",
        ),
        Pain(
            "Votre collègue fait 12 km de plus que vous, et vous le rappelle à chaque relève.",
            "Tous les trajets de la journée sur une seule vue, à imprimer ou partager avec le cabinet "
            "ou votre remplaçante. Les comptes sont vite faits.",
            "map-pin",
        ),
    ),
    demo=DemoScenario(
        debut=time(7, 30),
        positions=((30, 60), (90, 140), (155, 70), (220, 150), (290, 80)),
        incident=Incident(kind="retrait", position=2, label="Patient absent", icon="user-minus"),
        sms="Bonjour, mon passage chez vous est avancé à {heure}. Bouclé.tech",
    ),
    rentabilite=Hypotheses(km_par_semaine=40, heures_admin_par_mois=3, no_show_par_mois=2, valeur_passage=Decimal("12")),
)
