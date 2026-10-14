import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator

Metier = Literal["laveur-vitres", "infirmier", "aide-domicile", "jardinier", "ramoneur", "autre"]
Taille = Literal["solo", "2-5", "6+"]
Douleur = Literal["imprevus", "rentabilite", "planning", "coordination", "autre"]
Variante = Literal["generique", "laveur-vitres", "infirmier", "services-domicile"]

# Accepte 0X, +33X, +33 0X, +33 (0)X, 0033X ; [0-9] et non \d pour refuser les chiffres Unicode.
FRENCH_PHONE = re.compile(r"^(?:(?:\+33|0033)0?|0)([1-9][0-9]{8})$")
PHONE_SEPARATORS = re.compile(r"[\s.\-/()]")


class LeadIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metier: Metier
    taille: Taille
    douleur: Douleur
    email: EmailStr
    phone: str
    accepte_appel: bool = False
    consentement_rgpd: Literal[True]
    website: str = Field(default="", max_length=0)
    variante: Variante
    utm_source: str | None = Field(default=None, max_length=100)
    utm_campaign: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, email: str) -> str:
        return email.lower()

    @field_validator("phone")
    @classmethod
    def normalize_french_phone(cls, phone: str) -> str:
        match = FRENCH_PHONE.match(PHONE_SEPARATORS.sub("", phone))
        if match is None:
            raise ValueError("numéro de téléphone français invalide")
        return "+33" + match.group(1)


def invalid_fields(error: ValidationError) -> set[str]:
    return {str(detail["loc"][0]) for detail in error.errors() if detail["loc"]}
