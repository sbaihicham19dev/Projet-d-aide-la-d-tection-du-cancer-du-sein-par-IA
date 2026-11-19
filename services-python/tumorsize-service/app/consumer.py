"""
Consumer — Écoute les résultats segmentation depuis RabbitMQ
"""
import json
import logging

import aio_pika

logger = logging.getLogger("tumorsize.consumer")


class RabbitMQConsumer:
    def __init__(self, sizer,
                 url: str      = "amqp://guest:guest@rabbitmq/",
                 queue_in: str = "segmentation_results"):
        self.sizer    = sizer
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
            logger.info("✅ Consumer démarré — '%s'", self.queue_in)
        except Exception as e:
            logger.warning("⚠️ RabbitMQ indisponible : %s", e)
            raise

    async def _on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                data        = json.loads(message.body)
                mask_base64 = data.get("mask_base64")
                tumor_pct   = data.get("tumor_area_pct")

                if mask_base64:
                    result = self.sizer.calculate_from_mask(mask_base64)
                elif tumor_pct:
                    result = self.sizer.calculate_from_area_pct(tumor_pct)
                else:
                    return

                logger.info("✅ Taille : %.2f cm (%s)",
                            result.diameter_cm, result.tnm_stage)
            except Exception as e:
                logger.error("❌ Erreur : %s", e)

    async def stop(self):
        if self._conn:
            await self._conn.close()