"""
Consumer — Écoute les résultats pipeline depuis RabbitMQ
"""
import json
import logging
import aio_pika
from app.staging import stage_from_pipeline

logger = logging.getLogger("stage.consumer")


class RabbitMQConsumer:
    def __init__(self, url="amqp://guest:guest@rabbitmq/", queue_in="pipeline_results"):
        self.url      = url
        self.queue_in = queue_in
        self._conn    = None
        self._chan    = None

    async def start(self):
        try:
            self._conn = await aio_pika.connect_robust(self.url)
            self._chan = await self._conn.channel()
            await self._chan.set_qos(prefetch_count=1)
            queue = await self._chan.declare_queue(self.queue_in, durable=True)
            await queue.consume(self._on_message)
            logger.info("✅ Consumer démarré")
        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)
            raise

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data   = json.loads(message.body)
                ts     = data.get("tumorsize") or {}
                cls    = data.get("classification") or {}
                birads = data.get("birads") or {}
                result = stage_from_pipeline(
                    diameter_cm          = ts.get("diameter_cm", 0.0),
                    tnm_stage            = ts.get("tnm_stage"),
                    classification_class = cls.get("predicted_class"),
                    birads_score         = birads.get("birads_score"),
                )
                logger.info("✅ Stade : %s", result.stage)
            except Exception as e:
                logger.error("❌ Erreur : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()