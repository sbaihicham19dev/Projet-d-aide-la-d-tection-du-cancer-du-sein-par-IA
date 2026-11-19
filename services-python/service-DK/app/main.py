"""
main.py
Point d'entrée FastAPI.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.router import router

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "Breast Cancer Detection API"),
    description="Detection du cancer mammaire par ResNet50 — CBIS-DDSM",
    version=os.getenv("APP_VERSION", "1.0.0"),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["Detection"])


@app.get("/", tags=["Root"])
def root():
    return {
        "service": os.getenv("APP_NAME", "Breast Cancer Detection API"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "env":     os.getenv("APP_ENV", "development"),
        "docs":    "/docs",
        "health":  "/api/v1/health",
        "predict": "/api/v1/predict",
    }