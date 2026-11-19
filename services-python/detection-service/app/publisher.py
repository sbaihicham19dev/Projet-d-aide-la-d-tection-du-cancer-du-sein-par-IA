import pika
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
QUEUE_RESULTS = "queue.results"

def publish_result(result: dict):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_RESULTS, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_RESULTS,
            body=json.dumps(result),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
    except Exception as e:
        print(f"[WARNING] RabbitMQ non disponible : {e}")