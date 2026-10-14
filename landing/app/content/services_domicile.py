from app.content.models import Pain, Variant

VARIANT = Variant(
    slug="services-domicile",
    path="/services-domicile",
    metier_prefill=None,
    h1="Trois clients à caser, un seul après-midi ?",
    sous_titre="Bouclé trouve le bon ordre de passage et prévient vos clients par SMS. Vous arrivez à l'heure, sans courir.",
    douleurs=(
        Pain(
            "Les demandes arrivent en vrac, au téléphone.",
            "Ajoutez-les en quelques secondes : Bouclé leur trouve une place dans la semaine.",
        ),
        Pain(
            "Les pics de saison (taille, ramonage, entretien) débordent.",
            "Bouclé répartit les passages sur plusieurs semaines, sans oublier personne.",
        ),
        Pain(
            "Plusieurs intervenants, qui va où ?",
            "Chacun reçoit sa tournée, vous gardez la vue d'ensemble.",
        ),
    ),
)
