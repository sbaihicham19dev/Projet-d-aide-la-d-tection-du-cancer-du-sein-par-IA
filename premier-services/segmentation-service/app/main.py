"""
Segmentation Service — Point d'entrée FastAPI
"""
import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.router import router
from app.segmentor import Segmentor
from app.consumer import RabbitMQConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("segmentation.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    segmentor = Segmentor()
    segmentor.load()
    app.state.segmentor = segmentor
    logger.info("✅ Segmentor chargé")

    consumer = None
    try:
        consumer = RabbitMQConsumer(segmentor)
        asyncio.create_task(consumer.start())
        logger.info("✅ Consumer RabbitMQ démarré")
    except Exception as exc:
        logger.warning("⚠️ RabbitMQ désactivé (mode HTTP uniquement) : %s", exc)

    yield

    if consumer:
        await consumer.stop()
    logger.info("🛑 Service arrêté")


app = FastAPI(
    title="Breast Cancer Segmentation Service",
    description=(
        "Segmente la zone tumorale d'une mammographie via U-Net. "
        "Retourne un masque binaire PNG 224×224 (blanc = tumeur)."
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