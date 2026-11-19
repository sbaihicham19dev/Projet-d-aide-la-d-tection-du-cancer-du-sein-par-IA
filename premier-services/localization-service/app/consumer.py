"""
Consumer — Écoute les résultats segmentation depuis RabbitMQ
"""
import json
import logging

import aio_pika

logger = logging.getLogger("localization.consumer")


class RabbitMQConsumer:
    def __init__(self, localizer,
                 url: str      = "amqp://guest:guest@rabbitmq/",
                 queue_in: str = "segmentation_results"):
        self.localizer = localizer
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
            logger.info("✅ Consumer démarré — '%s'", self.queue_in)
        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)
            raise

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data        = json.loads(message.body)
                mask_base64 = data.get("mask_base64")
                if mask_base64:
                    result = self.localizer.localize_from_mask(mask_base64)
                    logger.info("✅ Localisation : %s", result.quadrant)
            except Exception as e:
                logger.error("❌ Erreur : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()