import pika
import json
import os
from app.predictor import predict
from app.publisher import publish_result

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
QUEUE_DETECTION = "queue.detection"

def start_consumer():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_DETECTION, durable=True)

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                image_base64 = message.get("image_base64")
                image_id = message.get("image_id")
                result = predict(image_base64)
                publish_result({
                    "image_id": image_id,
                    "prediction": result["prediction"],
                    "confidence": result["confidence"],
                    "status": "success"
                })
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"[ERROR] {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=QUEUE_DETECTION, on_message_callback=callback)
        print("[*] Waiting for messages in queue.detection ...")
        channel.start_consuming()
    except Exception as e:
        print(f"[WARNING] RabbitMQ consumer non démarré : {e}")