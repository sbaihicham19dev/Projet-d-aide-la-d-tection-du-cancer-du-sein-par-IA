import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.consumer import RabbitMQConsumer
from app.narrative import NarrativeGenerator
from app.publisher import RabbitMQPublisher
from app.router import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s - %(message)s")
logger = logging.getLogger("llm_narrative.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.generator = NarrativeGenerator()
    app.state.publisher = RabbitMQPublisher()
    consumer = None
    if os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            consumer = RabbitMQConsumer(app.state.generator, app.state.publisher)
            asyncio.create_task(consumer.start())
            logger.info("RabbitMQ consumer started")
        except Exception as exc:
            logger.warning("RabbitMQ disabled; HTTP mode only: %s", exc)
    else:
        logger.info("RabbitMQ disabled; HTTP mode only")
    yield
    if consumer:
        await consumer.stop()
    await app.state.publisher.close()


app = FastAPI(
    title="Breast Cancer LLM Narrative Service",
    description="Converts assembled JSON results into a structured clinical narrative. No chat interface.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
