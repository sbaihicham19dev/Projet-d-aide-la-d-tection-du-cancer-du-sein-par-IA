import asyncio
import logging
import os
from typing import Any, Dict

from fastapi import APIRouter, Request

from app.schemas import AssembledReport, HealthResponse, PipelineInputs

logger = logging.getLogger("assembler.router")

router = APIRouter(prefix="/api/v1", tags=["Assembler"])


@router.get("/health", response_model=HealthResponse)
async def health():
    from datetime import datetime, timezone
    return HealthResponse(status="ok", service="assembler-service", timestamp=datetime.now(timezone.utc).isoformat())


@router.post("/assemble", response_model=AssembledReport)
async def assemble(request: Request, payload: PipelineInputs):
    report = request.app.state.assembler.assemble(payload)
    publisher = getattr(request.app.state, "publisher", None)
    if publisher and os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            await asyncio.wait_for(publisher.publish(report.model_dump(mode="json")), timeout=1.0)
        except Exception as exc:
            logger.warning("RabbitMQ publish skipped: %s", exc)
    return report


@router.post("/ingest/{result_type}", response_model=Dict[str, Any])
async def ingest(result_type: str, request: Request, payload: Dict[str, Any]):
    buffer = request.app.state.buffer
    prediction_id = str(payload.get("prediction_id") or payload.get("id") or "unknown")
    item = buffer.setdefault(prediction_id, {})
    item[result_type] = payload
    item.setdefault("prediction_id", prediction_id)
    item.setdefault("filename", payload.get("filename"))
    return {"status": "accepted", "prediction_id": prediction_id, "received": sorted(item.keys())}
