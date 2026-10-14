import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.content import commun
from app.demo.route_geometry import demo_view
from app.icons import icon
from app.lead_repository import InMemoryLeadRepository, LeadRepository
from app.routes import build_router
from app.settings import Settings, SettingsError
from brand.identity import DOMAIN_SUFFIX, NAME, TAGLINE
from brand.logo import logo_svg

LANDING_DIR = Path(__file__).parent.parent
logger = logging.getLogger(__name__)


def build_repository(settings: Settings) -> LeadRepository:
    if settings.lead_store == "memory":
        logger.warning("LEAD_STORE=memory : les leads sont perdus à chaque redémarrage.")
        return InMemoryLeadRepository()
    raise SettingsError(f"LEAD_STORE={settings.lead_store!r} non supporté")


def create_app(settings: Settings, repository: LeadRepository) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(directory=LANDING_DIR / "static"), name="static")
    templates = Jinja2Templates(directory=LANDING_DIR / "app" / "templates")
    templates.env.globals.update(
        name=NAME,
        domain_suffix=DOMAIN_SUFFIX,
        tagline=TAGLINE,
        logo_svg=logo_svg(),
        commun=commun,
        contact_email=settings.contact_email,
        icon=icon,
        demo_view=demo_view,
    )
    app.state.templates = templates
    app.include_router(build_router(settings, repository, templates))
    return app
