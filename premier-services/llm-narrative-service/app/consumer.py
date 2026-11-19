import json
import logging
import os

import aio_pika

logger = logging.getLogger("llm_narrative.consumer")


class RabbitMQConsumer:
    def __init__(self, generator, publisher, url: str | None = None, queue_in: str = "assembled_results"):
        self.generator = generator
        self.publisher = publisher
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.queue_in = queue_in
        self._conn = None
        self._chan = None

    async def start(self):
        self._conn = await aio_pika.connect_robust(self.url)
        self._chan = await self._conn.channel()
        await self._chan.set_qos(prefetch_count=4)
        queue = await self._chan.declare_queue(self.queue_in, durable=True)
        await queue.consume(self._on_message)
        logger.info("Narrative consumer listening on %s", self.queue_in)

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            report = json.loads(message.body)
            narrative = await self.generator.generate(report)
            await self.publisher.publish(narrative.model_dump(mode="json"))

    async def stop(self):
        if self._conn:
            await self._conn.close()
