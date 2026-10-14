from fastapi.testclient import TestClient

from app.content import commun
from app.factory import build_repository, create_app
from app.lead_repository import InMemoryLeadRepository, StorageUnavailableError


class UnavailableRepository:
    def add(self, lead) -> None:
        raise StorageUnavailableError("stockage injoignable")

    def count(self) -> int:
        return 0


def test_valid_lead_is_stored(client, repository, lead_payload):
    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 201
    assert response.json() == {"redirect": "/merci"}
    assert repository.count() == 1


def test_invalid_fields_return_french_messages(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "phone": "06 12", "email": "paul@"})

    assert response.status_code == 400
    assert response.json()["errors"] == {
        "phone": commun.FIELD_MESSAGES["phone"],
        "email": commun.FIELD_MESSAGES["email"],
    }
    assert repository.count() == 0


def test_missing_consent_is_refused(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "consentement_rgpd": False})

    assert response.status_code == 400
    assert response.json()["errors"] == {"consentement_rgpd": commun.FIELD_MESSAGES["consentement_rgpd"]}
    assert repository.count() == 0


def test_honeypot_stores_nothing_and_reveals_nothing(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "website": "https://spam.example"})

    assert response.status_code == 400
    assert response.json() == {"errors": {}, "message": commun.FORMULAIRE_INVALIDE}
    assert repository.count() == 0


def test_duplicate_returns_409(client, lead_payload):
    client.post("/api/leads", json=lead_payload)
    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 409
    assert response.json() == {"message": commun.DEJA_INSCRIT}


def test_same_email_with_different_case_is_a_duplicate(client, repository, lead_payload):
    client.post("/api/leads", json=lead_payload)
    response = client.post("/api/leads", json={**lead_payload, "email": "  Paul.Durand@Example.com "})

    assert response.status_code == 409
    assert repository.count() == 1


def test_storage_down_returns_503_with_contact_email(settings, lead_payload):
    client = TestClient(create_app(settings, UnavailableRepository()))

    response = client.post("/api/leads", json=lead_payload)

    assert response.status_code == 503
    assert response.json() == {"message": commun.INDISPONIBLE.format(contact_email="contact@example.com")}


def test_malformed_json_returns_400(client):
    response = client.post("/api/leads", content=b"{pas du json", headers={"Content-Type": "application/json"})

    assert response.status_code == 400
    assert response.json()["message"] == commun.FORMULAIRE_INVALIDE


def test_non_object_body_returns_400(client, lead_payload):
    response = client.post("/api/leads", json=[lead_payload])

    assert response.status_code == 400
    assert response.json()["message"] == commun.FORMULAIRE_INVALIDE


def test_unknown_field_returns_400(client, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "admin": True})

    assert response.status_code == 400
    assert response.json()["errors"] == {"admin": commun.FORMULAIRE_INVALIDE}


def test_memory_store_is_built_from_settings(settings):
    assert isinstance(build_repository(settings), InMemoryLeadRepository)


def test_error_on_field_without_visible_slot_comes_with_a_global_message(client, repository, lead_payload):
    response = client.post("/api/leads", json={**lead_payload, "utm_campaign": "c" * 101})

    assert response.status_code == 400
    assert response.json()["message"] == commun.FORMULAIRE_INVALIDE
    assert repository.count() == 0


def test_lead_beyond_early_access_places_is_sent_to_waitlist_thank_you(client, lead_payload):
    from app.offer import PLACES_EARLY_ACCESS

    for index in range(PLACES_EARLY_ACCESS):
        response = client.post("/api/leads", json={**lead_payload, "email": f"lead{index}@example.com"})
        assert response.json() == {"redirect": "/merci"}

    response = client.post("/api/leads", json={**lead_payload, "email": "late@example.com"})

    assert response.json() == {"redirect": "/merci?attente=1"}
