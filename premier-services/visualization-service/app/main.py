import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.consumer import RabbitMQConsumer
from app.publisher import RabbitMQPublisher
from app.router import router
from app.visualizer import GradCamVisualizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s - %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.visualizer = GradCamVisualizer()
    app.state.publisher = RabbitMQPublisher()
    consumer = None
    if os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            consumer = RabbitMQConsumer(app.state.visualizer, app.state.publisher)
            asyncio.create_task(consumer.start())
        except Exception as exc:
            logging.getLogger("visualization.main").warning("RabbitMQ disabled; HTTP mode only: %s", exc)
    else:
        logging.getLogger("visualization.main").info("RabbitMQ disabled; HTTP mode only")
    yield
    if consumer:
        await consumer.stop()
    await app.state.publisher.close()


app = FastAPI(
    title="Breast Cancer Visualization Service",
    description="Creates Grad-CAM style heatmaps and overlays from mammography images and optional segmentation masks.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
