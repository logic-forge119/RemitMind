import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend directory and app directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "app"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.db import engine, Base, SessionLocal
from app.models import User
from app.routers import plans, transfers, analyst, receiver, agents, metrics, dev, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            print("Database empty on startup. Triggering initial synthetic data generation...")
            try:
                from data.generate import seed_database
                seed_database()
            except Exception as e:
                print(f"Auto-seed exception: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title="RemitMind API",
    description="AI-Powered Remittance Intelligence & Safety Layer for upay Bangladesh",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(plans.router)
app.include_router(transfers.router)
app.include_router(analyst.router)
app.include_router(receiver.router)
app.include_router(agents.router)
app.include_router(metrics.router)
app.include_router(dev.router)
app.include_router(ai.router)

# Health Check per 05_API_DOCS.md
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "RemitMind API",
        "version": "1.0.0",
        "environment": "production-ready",
        "ai_engines": ["IsolationForest", "RateForecaster", "DemandForecaster", "GroundedExplainer"]
    }

# Mount Static Frontend Assets
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

if FRONTEND_DIR.exists():
    if (FRONTEND_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    if (FRONTEND_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/", tags=["Frontend"])
    @app.get("/index.html", tags=["Frontend"])
    def serve_landing_page():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/app", tags=["Frontend"])
    @app.get("/app.html", tags=["Frontend"])
    def serve_main_app():
        return FileResponse(str(FRONTEND_DIR / "app.html"))

    @app.get("/login", tags=["Frontend"])
    @app.get("/login.html", tags=["Frontend"])
    def serve_login_page():
        return FileResponse(str(FRONTEND_DIR / "login.html"))

