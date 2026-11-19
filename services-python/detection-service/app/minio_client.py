from minio import Minio
from minio.error import S3Error
import os
import io
import logging

logger = logging.getLogger(__name__)

MINIO_URL      = os.getenv("MINIO_URL", "localhost:9000")
MINIO_USER     = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_PASSWORD = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET   = os.getenv("MINIO_BUCKET", "mammography")


class MinIOClient:
    """
    Récupère les images DICOM stockées dans MinIO
    à partir de leur UUID.
    """

    def __init__(self):
        self.client = Minio(
            MINIO_URL,
            access_key=MINIO_USER,
            secret_key=MINIO_PASSWORD,
            secure=False  # HTTP en local
        )
        logger.info(f"MinIO connecté sur {MINIO_URL} · bucket: {MINIO_BUCKET}")

    def get_image(self, image_uuid: str) -> bytes:
        """Télécharge l'image DICOM depuis MinIO par son UUID."""
        object_name = f"{image_uuid}.dcm"
        try:
            response = self.client.get_object(MINIO_BUCKET, object_name)
            image_bytes = response.read()
            logger.info(f"Image {object_name} récupérée ({len(image_bytes)} bytes)")
            return image_bytes
        except S3Error as e:
            logger.error(f"Erreur MinIO pour {object_name}: {e}")
            raise FileNotFoundError(f"Image {image_uuid} introuvable dans MinIO")
        finally:
            response.close()
            response.release_conn()


# Singleton
minio_client = MinIOClient()
