"""
Publisher — Publie les scores BI-RADS vers RabbitMQ
"""
import json
import logging

import aio_pika

logger = logging.getLogger("birads.publisher")


class RabbitMQPublisher:
    def __init__(self, url: str   = "amqp://guest:guest@rabbitmq/",
                 queue: str = "birads_results"):
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
            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self._chan.default_exchange.publish(
                message, routing_key=self.queue
            )
            logger.info("📤 BI-RADS publié → %s", self.queue)
        except Exception as e:
            logger.error("❌ Erreur publication : %s", e)

    async def close(self):
        if self._conn:
            await self._conn.close()