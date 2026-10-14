from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.content import VARIANTS, commun, legal
from app.content.models import Variant
from app.lead_repository import DuplicateLeadError, LeadRepository, StorageUnavailableError
from app.lead_schema import LeadIn, invalid_fields
from app.offer import places_restantes
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

    def variant_page(variant: Variant):
        def endpoint(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(
                request,
                "landing.html",
                {
                    "variant": variant,
                    "places": places_restantes(repository.count()),
                    "utm_source": request.query_params.get("utm_source", ""),
                    "utm_campaign": request.query_params.get("utm_campaign", ""),
                },
            )

        return endpoint

    for variant in VARIANTS.values():
        router.add_api_route(variant.path, variant_page(variant), methods=["GET"], response_class=HTMLResponse)

    @router.get("/merci", response_class=HTMLResponse)
    def thank_you(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "merci.html", {"calcom_url": settings.calcom_url})

    def legal_page(title: str, paragraphs: tuple[str, ...]):
        def endpoint(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(request, "legal.html", {"title": title, "paragraphs": paragraphs})

        return endpoint

    for path, (title, paragraphs) in legal.PAGES.items():
        router.add_api_route(path, legal_page(title, paragraphs), methods=["GET"], response_class=HTMLResponse)

    return router


def _invalid_form() -> JSONResponse:
    return JSONResponse({"errors": {}, "message": commun.FORMULAIRE_INVALIDE}, status_code=400)
