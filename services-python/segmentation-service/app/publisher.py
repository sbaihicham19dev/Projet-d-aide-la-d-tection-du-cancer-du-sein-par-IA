"""
Publisher — Publie les résultats de segmentation vers RabbitMQ
"""
import json
import logging

import aio_pika

logger = logging.getLogger("segmentation.publisher")


class RabbitMQPublisher:
    def __init__(self, url: str   = "amqp://guest:guest@rabbitmq/",
                 queue: str = "segmentation_results"):
        self.url   = url
        self.queue = queue
        self._conn = None
        self._chan = None

    async def connect(self):
        try:
            self._conn = await aio_pika.connect_robust(self.url)
            self._chan = await self._conn.channel()
            await self._chan.declare_queue(self.queue, durable=True)
            logger.info("✅ Publisher connecté")
        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)

    async def publish(self, data: dict):
        if self._chan is None:
            return
        try:
            # Ne pas envoyer le masque base64 complet dans RabbitMQ
            payload = {k: v for k, v in data.items() if k != "mask_base64"}
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self._chan.default_exchange.publish(
                message, routing_key=self.queue
            )
            logger.info("📤 Résultat publié → %s", self.queue)
        except Exception as e:
            logger.error("❌ Erreur publication : %s", e)

    async def close(self):
        if self._conn:
            await self._conn.close()