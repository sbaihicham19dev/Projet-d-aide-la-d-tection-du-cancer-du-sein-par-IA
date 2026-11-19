"""
Consumer — Consomme les détections Cancer depuis RabbitMQ et segmente
"""
import json
import logging
import io

import aio_pika
from PIL import Image

logger = logging.getLogger("segmentation.consumer")


class RabbitMQConsumer:
    def __init__(self, segmentor,
                 url: str      = "amqp://guest:guest@rabbitmq/",
                 queue_in: str = "detection_results"):
        self.segmentor = segmentor
        self.url       = url
        self.queue_in  = queue_in
        self._conn     = None
        self._chan     = None

    async def start(self):
        try:
            self._conn = await aio_pika.connect_robust(self.url)
            self._chan = await self._conn.channel()
            await self._chan.set_qos(prefetch_count=1)
            queue = await self._chan.declare_queue(self.queue_in, durable=True)
            await queue.consume(self._on_message)
            logger.info("✅ Consumer démarré — écoute '%s'", self.queue_in)
        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)
            raise

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body)
                if data.get("predicted_class") != "Cancer":
                    return

                if "image_bytes" in data:
                    img_bytes = bytes(data["image_bytes"])
                    image     = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    result    = self.segmentor.segment(image)
                    logger.info(
                        "✅ Segmentation : %d px (%.2f%%)",
                        result["tumor_area_px"],
                        result["tumor_area_pct"],
                    )
            except Exception as e:
                logger.error("❌ Erreur : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()
            logger.info("🛑 Consumer arrêté")