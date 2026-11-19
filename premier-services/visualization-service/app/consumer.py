import io
import json
import logging
import os

import aio_pika
from PIL import Image

logger = logging.getLogger("visualization.consumer")


class RabbitMQConsumer:
    def __init__(self, visualizer, publisher, url: str | None = None, queue_in: str = "detection_results"):
        self.visualizer = visualizer
        self.publisher = publisher
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.queue_in = queue_in
        self._conn = None
        self._chan = None

    async def start(self):
        self._conn = await aio_pika.connect_robust(self.url)
        self._chan = await self._conn.channel()
        await self._chan.set_qos(prefetch_count=2)
        queue = await self._chan.declare_queue(self.queue_in, durable=True)
        await queue.consume(self._on_message)
        logger.info("Visualization consumer listening on %s", self.queue_in)

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            data = json.loads(message.body)
            if data.get("predicted_class") not in {"Cancer", "Malignant"}:
                return
            if "image_bytes" not in data:
                logger.info("Visualization skipped: message has no image_bytes")
                return
            image = Image.open(io.BytesIO(bytes(data["image_bytes"]))).convert("RGB")
            result = self.visualizer.visualize(
                image=image,
                mask_base64=data.get("mask_base64"),
                tumor_area_pct=data.get("tumor_area_pct"),
                include_images=False,
            )
            result.update({
                "prediction_id": data.get("prediction_id", "unknown"),
                "filename": data.get("filename", "unknown"),
            })
            await self.publisher.publish(result)

    async def stop(self):
        if self._conn:
            await self._conn.close()
