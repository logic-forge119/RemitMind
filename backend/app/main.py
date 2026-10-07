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
from app.models import (
    User, Agent, Goal, RateHistory, Transfer,
    RiskAlert, ReviewAction, AgentCashDaily, ModelRun
)
from app.routers import plans, transfers, analyst, receiver, agents, metrics, dev, ai, scamshield, graph, resilience, compliance, docs, policy, websocket

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce mandatory secrets validation (fails fast if in production with insecure defaults)
    settings.validate_production_secrets()

    # Ensure all 9 tables exist in database
    Base.metadata.create_all(bind=engine)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_quarantined INTEGER DEFAULT 0"))
            conn.commit()
    except Exception:
        pass
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN quarantine_reason TEXT"))
            conn.commit()
    except Exception:
        pass
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

from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.auth import auth_router

app = FastAPI(
    title="RemitMind API",
    description="AI-Powered Remittance Intelligence & Safety Layer for upay Bangladesh",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Attach slowapi rate limiter to state
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request, exc: RateLimitExceeded):
    """Bilingual 429 Rate Limit Exceeded response."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Too many requests. Rate limit exceeded (10 req/min on transfers). Please wait before trying again.",
            "detail_bn": "অনুরোধের সীমা অতিক্রম করেছে (প্রতি মিনিটে সর্বোচ্চ ১০টি)। অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করে পুনরায় চেষ্টা করুন।",
            "retry_after_seconds": 60
        },
        headers={"Retry-After": "60"}
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
app.include_router(auth_router)
app.include_router(plans.router)
app.include_router(transfers.router)
app.include_router(analyst.router)
app.include_router(receiver.router)
app.include_router(agents.router)
app.include_router(metrics.router)
app.include_router(dev.router)
app.include_router(ai.router)
app.include_router(scamshield.router)
app.include_router(graph.router)
app.include_router(resilience.router)
app.include_router(compliance.router)
app.include_router(docs.router)
app.include_router(policy.router)
app.include_router(websocket.router)


# Health & Readiness Probes
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "RemitMind API",
        "version": "1.0.0",
        "environment": "production-ready",
        "ai_engines": ["IsolationForest", "RateForecaster", "DemandForecaster", "GroundedExplainer"]
    }

@app.get("/health/ready", tags=["Health"])
def readiness_check():
    # Verify database connection
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        # Simple query to verify DB is responsive
        u_count = db.query(User).count()
        return {
            "status": "ready",
            "database": "connected",
            "users_count": u_count,
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})
    finally:
        db.close()

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

