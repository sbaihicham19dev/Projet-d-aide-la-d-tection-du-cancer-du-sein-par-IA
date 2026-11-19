import json
import logging
import os
from typing import Dict

import aio_pika

from app.schemas import PipelineInputs

logger = logging.getLogger("assembler.consumer")


QUEUE_TO_FIELD: Dict[str, str] = {
    "detection_results": "detection",
    "classification_results": "classification",
    "segmentation_results": "segmentation",
    "birads_results": "birads",
    "localization_results": "localization",
    "tumorsize_results": "tumorsize",
    "visualization_results": "visualization",
}


class RabbitMQConsumer:
    def __init__(self, assembler, publisher, buffer: dict, url: str | None = None):
        self.assembler = assembler
        self.publisher = publisher
        self.buffer = buffer
        self.url = url or os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self._conn = None
        self._chan = None

    async def start(self):
        self._conn = await aio_pika.connect_robust(self.url)
        self._chan = await self._conn.channel()
        await self._chan.set_qos(prefetch_count=16)
        for queue_name, field in QUEUE_TO_FIELD.items():
            queue = await self._chan.declare_queue(queue_name, durable=True)
            await queue.consume(lambda msg, f=field: self._on_message(msg, f))
        logger.info("Assembler consumer listening on %s", ", ".join(QUEUE_TO_FIELD))

    async def _on_message(self, message: aio_pika.IncomingMessage, field: str):
        async with message.process():
            data = json.loads(message.body)
            prediction_id = str(data.get("prediction_id") or data.get("id") or "unknown")
            item = self.buffer.setdefault(prediction_id, {"prediction_id": prediction_id})
            item[field] = data
            if data.get("filename"):
                item["filename"] = data["filename"]

            payload = PipelineInputs(**item)
            report = self.assembler.assemble(payload)
            if report.completeness >= float(os.getenv("ASSEMBLER_MIN_COMPLETENESS", "0.7")):
                await self.publisher.publish(report.model_dump(mode="json"))

    async def stop(self):
        if self._conn:
            await self._conn.close()
