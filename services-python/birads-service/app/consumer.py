"""
Consumer — Écoute les résultats pipeline depuis RabbitMQ
"""
import json
import logging

import aio_pika

logger = logging.getLogger("birads.consumer")


class RabbitMQConsumer:
    def __init__(self, predictor,
                 url: str      = "amqp://guest:guest@rabbitmq/",
                 queue_in: str = "pipeline_results"):
        self.predictor = predictor
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
                data = json.loads(message.body)
                result = self.predictor.predict_from_pipeline(
                    image                = None,
                    detection_class      = data.get("predicted_class", "Non-Cancer"),
                    detection_conf       = data.get("confidence", 0.5),
                    classification_class = (data.get("classification") or {}).get("predicted_class"),
                    classification_conf  = (data.get("classification") or {}).get("confidence"),
                    tumor_area_pct       = (data.get("segmentation") or {}).get("tumor_area_pct"),
                )
                logger.info("✅ BI-RADS %s (%s)", result["birads_score"], result["birads_category"])
            except Exception as e:
                logger.error("❌ Erreur : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()