"""
Localization Service — Point d'entrée FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.localizer import Localizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("localization.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    localizer = Localizer()
    localizer.load()
    app.state.localizer = localizer
    logger.info("✅ Localizer chargé")
    yield
    logger.info("🛑 Service arrêté")


app = FastAPI(
    title="Breast Cancer Localization Service",
    description=(
        "Localise la tumeur mammaire dans le sein.\n"
        "Retourne le quadrant (UO/UI/LO/LI/C) et le centroïde."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)