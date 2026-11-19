"""
Classification Service — Point d'entrée FastAPI
"""
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.classifier import Classifier
from app.consumer import RabbitMQConsumer

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("classification.main")

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    classifier = Classifier()
    classifier.load()
    app.state.classifier = classifier
    logger.info("✅ Classifier chargé")

    consumer = None
    try:
        consumer = RabbitMQConsumer(classifier)
        asyncio.create_task(consumer.start())
        logger.info("✅ Consumer RabbitMQ démarré")
    except Exception as exc:
        logger.warning("⚠️ RabbitMQ désactivé (mode Swagger uniquement) : %s", exc)

    yield

    if consumer:
        await consumer.stop()
    logger.info("🛑 Service arrêté")


# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Breast Cancer Classification Service",
    description=(
        "Classifie une mammographie détectée comme Cancer en : "
        "Bénin (Benign) ou Malin (Malignant) "
        "à partir d'un modèle EfficientNet-B4."
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