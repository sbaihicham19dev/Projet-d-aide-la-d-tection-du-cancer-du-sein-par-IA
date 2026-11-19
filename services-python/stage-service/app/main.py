"""
Stage Service — Point d'entrée FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("stage.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Stage Service prêt — TNM AJCC 8e édition")
    yield
    logger.info("🛑 Service arrêté")


app = FastAPI(
    title="Breast Cancer Stage Service",
    description="Détermine le stade TNM du cancer du sein (I→IV) selon AJCC 8e édition.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)