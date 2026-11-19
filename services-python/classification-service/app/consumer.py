"""
Consumer — Consomme les détections depuis RabbitMQ et classifie
"""
import json
import logging
import io

import aio_pika
from PIL import Image

logger = logging.getLogger("classification.consumer")


class RabbitMQConsumer:
    def __init__(self, classifier,
                 url: str   = "amqp://guest:guest@rabbitmq/",
                 queue_in:  str = "detection_results",
                 queue_out: str = "classification_results"):
        self.classifier = classifier
        self.url        = url
        self.queue_in   = queue_in
        self.queue_out  = queue_out
        self._conn      = None
        self._chan      = None

    async def start(self):
        try:
            self._conn = await aio_pika.connect_robust(self.url)
            self._chan = await self._conn.channel()
            await self._chan.set_qos(prefetch_count=1)

            queue = await self._chan.declare_queue(self.queue_in, durable=True)
            await queue.consume(self._on_message)
            logger.info("✅ Consumer démarré — écoute sur '%s'", self.queue_in)

        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)
            raise

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body)
                logger.info("📥 Message reçu : %s", data.get("filename", "?"))

                # Si le message contient une image en bytes
                if "image_bytes" in data:
                    img_bytes = bytes(data["image_bytes"])
                    image     = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    result    = self.classifier.predict(image)
                    logger.info("✅ Classification : %s (%.2f)", result["class"], result["confidence"])

            except Exception as e:
                logger.error("❌ Erreur traitement message : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()
            logger.info("🛑 Consumer arrêté")