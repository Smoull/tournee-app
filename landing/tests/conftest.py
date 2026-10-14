import pytest
from fastapi.testclient import TestClient

from app.factory import create_app
from app.lead_repository import InMemoryLeadRepository
from app.settings import Settings


@pytest.fixture
def settings():
    return Settings(lead_store="memory", calcom_url="https://cal.com/example/15min", contact_email="contact@example.com")


@pytest.fixture
def repository():
    return InMemoryLeadRepository()


@pytest.fixture
def client(settings, repository):
    return TestClient(create_app(settings, repository))


@pytest.fixture
def lead_payload():
    return {
        "metier": "jardinier",
        "taille": "solo",
        "douleur": "rentabilite",
        "email": "paul.durand@example.com",
        "phone": "07 11 22 33 44",
        "accepte_appel": False,
        "consentement_rgpd": True,
        "website": "",
        "variante": "services-domicile",
        "utm_source": "agence",
        "utm_campaign": "lancement",
    }
