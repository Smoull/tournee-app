import pytest
from pydantic import ValidationError

from app.lead_schema import LeadIn, invalid_fields

VALID = {
    "metier": "laveur-vitres",
    "taille": "solo",
    "douleur": "imprevus",
    "email": "jean.dupont@example.com",
    "phone": "06 12 34 56 78",
    "accepte_appel": True,
    "consentement_rgpd": True,
    "website": "",
    "variante": "laveur-vitres",
}


def errors_for(payload: dict) -> set[str]:
    with pytest.raises(ValidationError) as error:
        LeadIn.model_validate(payload)
    return invalid_fields(error.value)


def test_valid_lead_is_accepted():
    lead = LeadIn.model_validate(VALID)
    assert lead.metier == "laveur-vitres"
    assert lead.accepte_appel is True


@pytest.mark.parametrize("field", ["metier", "taille", "douleur", "email", "phone", "consentement_rgpd", "variante"])
def test_required_field_missing(field):
    payload = {key: value for key, value in VALID.items() if key != field}
    assert field in errors_for(payload)


def test_accepte_appel_is_optional():
    payload = {key: value for key, value in VALID.items() if key != "accepte_appel"}
    assert LeadIn.model_validate(payload).accepte_appel is False


def test_consent_false_is_refused():
    assert "consentement_rgpd" in errors_for({**VALID, "consentement_rgpd": False})


@pytest.mark.parametrize("field,value", [("metier", "plombier"), ("taille", "12"), ("douleur", "ennui"), ("variante", "x")])
def test_unknown_choice_is_refused(field, value):
    assert field in errors_for({**VALID, field: value})


def test_email_is_trimmed_and_lowercased():
    assert LeadIn.model_validate({**VALID, "email": "  Jean.Dupont@Example.COM "}).email == "jean.dupont@example.com"


def test_invalid_email_is_refused():
    assert "email" in errors_for({**VALID, "email": "jean.dupont@"})


@pytest.mark.parametrize(
    "raw", ["0612345678", "06 12 34 56 78", "06.12.34.56.78", "06-12-34-56-78", "+33 6 12 34 56 78", "+33612345678"]
)
def test_french_phone_formats_are_normalized(raw):
    assert LeadIn.model_validate({**VALID, "phone": raw}).phone == "+33612345678"


@pytest.mark.parametrize("raw", ["06 12 34", "0012345678", "+44 7911 123456", "06 12 34 56 78 90", "téléphone"])
def test_invalid_phone_is_refused(raw):
    assert "phone" in errors_for({**VALID, "phone": raw})


def test_filled_honeypot_is_refused():
    assert "website" in errors_for({**VALID, "website": "https://spam.example"})


def test_unknown_field_is_refused():
    assert "admin" in errors_for({**VALID, "admin": True})


def test_too_long_utm_is_refused():
    assert "utm_source" in errors_for({**VALID, "utm_source": "a" * 101})


def test_non_object_payload_has_no_field_errors():
    assert errors_for([VALID]) == set()
