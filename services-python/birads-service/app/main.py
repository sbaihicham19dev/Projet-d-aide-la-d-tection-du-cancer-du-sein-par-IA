"""
BI-RADS Service — Point d'entrée FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.birads_predictor import BIRADSPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("birads.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor = BIRADSPredictor()
    predictor.load()
    app.state.predictor = predictor
    logger.info("✅ BI-RADS Predictor chargé (méthode: %s)",
                "CNN+ACR" if predictor.model else "ACR_rules")
    yield
    logger.info("🛑 Service arrêté")


app = FastAPI(
    title="Breast Cancer BI-RADS Service",
    description=(
        "Calcule le score BI-RADS (0-6) selon les règles ACR 2024 "
        "combinées avec un CNN ResNet-50."
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