import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.assembler import ReportAssembler
from app.consumer import RabbitMQConsumer
from app.publisher import RabbitMQPublisher
from app.router import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s - %(message)s")
logger = logging.getLogger("assembler.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.assembler = ReportAssembler()
    app.state.buffer = {}
    app.state.publisher = RabbitMQPublisher()
    consumer = None
    if os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            consumer = RabbitMQConsumer(app.state.assembler, app.state.publisher, app.state.buffer)
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
    title="Breast Cancer Assembler Service",
    description="Fuses pipeline outputs, computes TNM staging, and publishes a validated report.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
