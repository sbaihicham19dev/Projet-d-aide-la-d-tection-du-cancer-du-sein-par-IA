"""
Publisher — Publie les résultats de staging vers RabbitMQ
"""
import json
import logging
import aio_pika

logger = logging.getLogger("stage.publisher")


class RabbitMQPublisher:
    def __init__(self, url="amqp://guest:guest@rabbitmq/", queue="stage_results"):
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
            await self._chan.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(data).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue,
            )
            logger.info("📤 Stade publié → %s", self.queue)
        except Exception as e:
            logger.error("❌ Erreur : %s", e)

    async def close(self):
        if self._conn:
            await self._conn.close()