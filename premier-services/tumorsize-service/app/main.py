"""
TumorSize Service — Point d'entrée FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.sizer import Sizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("tumorsize.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    sizer = Sizer()
    sizer.load()
    app.state.sizer = sizer
    logger.info("✅ Sizer chargé — conversion px → cm prête")
    yield
    logger.info("🛑 Service arrêté")


app = FastAPI(
    title="Breast Cancer TumorSize Service",
    description=(
        "Convertit la taille de la tumeur de pixels en centimètres.\n"
        "Utilise le PixelSpacing DICOM et la classification TNM."
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