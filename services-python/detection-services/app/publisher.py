"""
Publisher RabbitMQ — publie les résultats de prédiction
"""
import json
import logging
import os

logger = logging.getLogger("detection.publisher")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RESULT_QUEUE = os.getenv("RESULT_QUEUE", "detection.results")

try:
    import aio_pika

    _PIKA_AVAILABLE = True
except ImportError:
    _PIKA_AVAILABLE = False
    logger.warning("aio_pika non installé — publication RabbitMQ désactivée.")


class ResultPublisher:
    """Publie un message JSON dans la queue des résultats."""

    def __init__(self):
        self._connection = None
        self._channel = None

    async def connect(self) -> None:
        if not _PIKA_AVAILABLE:
            return
        self._connection = await aio_pika.connect_robust(RABBITMQ_URL)
        self._channel = await self._connection.channel()
        await self._channel.declare_queue(RESULT_QUEUE, durable=True)
        logger.info("Publisher connecté à RabbitMQ — queue=%s", RESULT_QUEUE)

    async def publish(self, payload: dict) -> None:
        if not _PIKA_AVAILABLE or self._channel is None:
            logger.debug("Publication ignorée (RabbitMQ indisponible) : %s", payload)
            return
        body = json.dumps(payload).encode()
        await self._channel.default_exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=RESULT_QUEUE,
        )
        logger.info("Résultat publié → %s", RESULT_QUEUE)

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()