from app.content import generique, infirmier, laveur_vitres, services_domicile
from app.content.models import Variant

VARIANTS: dict[str, Variant] = {
    module.VARIANT.slug: module.VARIANT for module in (generique, laveur_vitres, infirmier, services_domicile)
}
