import asyncio
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.schemas import HealthResponse, NarrativeRequest, NarrativeResponse

router = APIRouter(prefix="/api/v1", tags=["LLM Narrative"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    generator = request.app.state.generator
    return HealthResponse(
        status="ok",
        service="llm-narrative-service",
        llm_enabled=generator.llm_enabled,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/narrative", response_model=NarrativeResponse)
async def narrative(request: Request, payload: NarrativeRequest):
    result = await request.app.state.generator.generate(
        payload.report,
        language=payload.language,
        include_disclaimer=payload.include_disclaimer,
    )
    publisher = getattr(request.app.state, "publisher", None)
    if publisher and os.getenv("ENABLE_RABBITMQ", "false").lower() == "true":
        try:
            await asyncio.wait_for(publisher.publish(result.model_dump(mode="json")), timeout=1.0)
        except Exception:
            pass
    return result
