"""
Detection Service — Point d'entrée FastAPI (Swagger SAFE MODE)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.predictor import Predictor

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

logger = logging.getLogger("detection.main")

# ── Singleton Predictor ─────────────────────────────────
predictor = Predictor()


# ── Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / Shutdown SAFE (Swagger mode)
    """

    # ── Charger modèle de façon sécurisée ──
    try:
        predictor.load()
        app.state.predictor = predictor
        logger.info("✅ Modèle chargé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur chargement modèle: {e}")
        logger.warning("⚠️ Mode fallback activé (Swagger OK)")
        app.state.predictor = predictor

    # ── RabbitMQ DÉSACTIVÉ pour Swagger ──
    logger.info("⚠️ RabbitMQ désactivé (mode Swagger uniquement)")

    yield

    # ── Shutdown ──
    logger.info("🛑 Service arrêté proprement")


# ── FastAPI app ─────────────────────────────────────────
app = FastAPI(
    title="Breast Cancer Detection Service",
    description="API de classification mammographie (Cancer / Non-Cancer)",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────
app.include_router(router)


# ── Health check (IMPORTANT pour Swagger) ───────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "detection-service"
    }