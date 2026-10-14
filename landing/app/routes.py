from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.content import commun
from app.lead_repository import DuplicateLeadError, LeadRepository, StorageUnavailableError
from app.lead_schema import LeadIn, invalid_fields
from app.settings import Settings


def build_router(settings: Settings, repository: LeadRepository, templates: Jinja2Templates) -> APIRouter:
    router = APIRouter()

    @router.post("/api/leads")
    async def create_lead(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
        except ValueError:
            return _invalid_form()

        try:
            lead = LeadIn.model_validate(payload)
        except ValidationError as error:
            fields = invalid_fields(error)
            # Honeypot rempli ou corps non exploitable : réponse neutre, rien n'est révélé au robot.
            if not fields or "website" in fields:
                return _invalid_form()
            errors = {field: commun.FIELD_MESSAGES.get(field, commun.FORMULAIRE_INVALIDE) for field in fields}
            return JSONResponse({"errors": errors}, status_code=400)

        try:
            repository.add(lead)
        except DuplicateLeadError:
            return JSONResponse({"message": commun.DEJA_INSCRIT}, status_code=409)
        except StorageUnavailableError:
            message = commun.INDISPONIBLE.format(contact_email=settings.contact_email)
            return JSONResponse({"message": message}, status_code=503)

        return JSONResponse({"redirect": "/merci"}, status_code=201)

    return router


def _invalid_form() -> JSONResponse:
    return JSONResponse({"errors": {}, "message": commun.FORMULAIRE_INVALIDE}, status_code=400)
