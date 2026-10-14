import pytest

from app.lead_repository import DuplicateLeadError, InMemoryLeadRepository
from app.lead_schema import LeadIn

PAYLOAD = {
    "metier": "infirmier",
    "taille": "2-5",
    "douleur": "planning",
    "email": "marie.martin@example.com",
    "phone": "0698765432",
    "consentement_rgpd": True,
    "variante": "infirmier",
}


def test_add_then_count():
    repository = InMemoryLeadRepository()
    repository.add(LeadIn.model_validate(PAYLOAD))
    assert repository.count() == 1


def test_duplicate_email_is_refused_without_leaking_it():
    repository = InMemoryLeadRepository()
    repository.add(LeadIn.model_validate(PAYLOAD))

    with pytest.raises(DuplicateLeadError) as error:
        repository.add(LeadIn.model_validate({**PAYLOAD, "email": "Marie.Martin@Example.com"}))

    assert "marie" not in str(error.value).lower()
    assert repository.count() == 1
