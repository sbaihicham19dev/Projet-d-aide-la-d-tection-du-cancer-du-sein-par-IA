import json
import logging
import os

import aio_pika

logger = logging.getLogger("assembler.publisher")


class RabbitMQPublisher:
    def __init__(self, url: str | None = None, queue: str = "assembled_results"):
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.queue = queue
        self._conn = None
        self._chan = None

    async def connect(self):
        self._conn = await aio_pika.connect_robust(self.url)
        self._chan = await self._conn.channel()
        await self._chan.declare_queue(self.queue, durable=True)

    async def publish(self, payload: dict):
        if self._chan is None:
            await self.connect()
        await self._chan.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(payload, default=str).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self.queue,
        )
        logger.info("Assembled report published to %s", self.queue)

    async def close(self):
        if self._conn:
            await self._conn.close()
