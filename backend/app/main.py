from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.core.config import settings
from app.db.session import SessionLocal, ensure_database_exists
from app.models import Base
from app.db.session import engine
from app.services.seed import seed
from app.services.alerts import scan_due_alerts
from app.api.routes import api, public


@asynccontextmanager
async def lifespan(app):
    ensure_database_exists()
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        seed(db)
        scan_due_alerts(db)
    finally:
        db.close()

    async def alert_loop():
        while True:
            await asyncio.sleep(3600)
            db = SessionLocal()
            try:
                scan_due_alerts(db)
            finally:
                db.close()

    task = asyncio.create_task(alert_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title="Dr. Bhasin's Lab Asset Management", version="1.0.0", lifespan=lifespan
)
app_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(app_dir / "templates"))
app.mount("/static", StaticFiles(directory=str(app_dir / "static")), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api)
app.include_router(public)


@app.get("/", response_class=HTMLResponse)
def portal(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "user_database": "local",
    }
