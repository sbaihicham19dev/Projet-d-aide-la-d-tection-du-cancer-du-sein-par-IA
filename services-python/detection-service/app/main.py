from fastapi import FastAPI
from app.router import router
import threading
from app.consumer import start_consumer

app = FastAPI(
    title="Detection Service",
    description="ResNet50 - Cancer / Non-Cancer Detection",
    version="1.0.0",
    docs_url="/docs"
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()

@app.get("/health")
def health_check():
    return {"status": "ok"}