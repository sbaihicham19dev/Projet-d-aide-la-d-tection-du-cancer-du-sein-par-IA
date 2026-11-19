"""
Consumer RabbitMQ — consomme les images à analyser
"""
import base64
import io
import json
import logging
import os

from PIL import Image

from app.predictor import Predictor
from app.publisher import ResultPublisher

logger = logging.getLogger("detection.consumer")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
INPUT_QUEUE = os.getenv("INPUT_QUEUE", "detection.tasks")

try:
    import aio_pika
    _PIKA_AVAILABLE = True
except ImportError:
    _PIKA_AVAILABLE = False


class RabbitMQConsumer:
    """Écoute la queue d'entrée et lance la prédiction sur chaque message."""

    def __init__(self, predictor: Predictor):
        self.predictor = predictor
        self.publisher = ResultPublisher()
        self._connection = None
        self._running = False

    async def start(self) -> None:
        if not _PIKA_AVAILABLE:
            logger.warning("aio_pika absent — consommateur RabbitMQ désactivé.")
            return

        self._connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=4)
        queue = await channel.declare_queue(INPUT_QUEUE, durable=True)

        await self.publisher.connect()
        self._running = True
        logger.info("Consumer en écoute sur la queue : %s", INPUT_QUEUE)

        async with queue.iterator() as q_iter:
            async for message in q_iter:
                if not self._running:
                    break
                async with message.process():
                    await self._handle(message.body)

    async def stop(self) -> None:
        self._running = False
        if self._connection:
            await self._connection.close()
        await self.publisher.close()

    # ── Traitement d'un message ───────────────────────────────────────────────

    async def _handle(self, body: bytes) -> None:
        try:
            payload = json.loads(body)
            image_b64: str = payload["image_b64"]
            correlation_id: str = payload.get("correlation_id", "unknown")
            filename: str = payload.get("filename", "unknown")

            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            result = self.predictor.predict(image)

            await self.publisher.publish({
                "correlation_id": correlation_id,
                "filename": filename,
                "predicted_class": result["class"],
                "confidence": result["confidence"],
                "probabilities": result["probabilities"],
            })

            logger.info(
                "Message traité — id=%s  classe=%s  conf=%.4f",
                correlation_id, result["class"], result["confidence"],
            )

        except Exception as exc:
            logger.error("Erreur traitement message : %s", exc, exc_info=True)