from app.content.models import Pain, Variant

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
        ),
        Pain(
            "Les passages tous les 2 mois, il faut s'en souvenir.",
            "Les clients récurrents reviennent tout seuls dans votre planning, au bon rythme.",
        ),
        Pain(
            "Porte fermée, client absent, trajet pour rien.",
            "La veille, un SMS confirme le passage. Le client absent se signale avant, pas après.",
        ),
    ),
)
