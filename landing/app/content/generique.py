from app.content.models import Pain, Variant

VARIANT = Variant(
    slug="generique",
    path="/",
    metier_prefill=None,
    h1="Un imprévu à 7h, et toute la journée déraille ?",
    sous_titre="Bouclé recalcule votre tournée et prévient vos clients par SMS. Vous, vous conduisez.",
    douleurs=(
        Pain(
            "Un client annule, un autre ajoute un passage.",
            "Votre tournée se réorganise en un geste. Les clients concernés reçoivent leur nouvel horaire par SMS.",
        ),
        Pain(
            "Des kilomètres en trop, sans s'en rendre compte.",
            "Bouclé ordonne vos arrêts et chiffre le coût de chaque journée : carburant, temps, rentabilité.",
        ),
        Pain(
            "Le planning de la semaine tient dans votre tête.",
            "Il tient sur une page : imprimable chaque matin, partageable avec vos collègues.",
        ),
    ),
)
