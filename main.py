
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, SessionLocal, engine
from app.models.product import Product
from app.admin import router as admin_router

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

templates = Jinja2Templates(directory=str(ROOT / "templates"))
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

secret = os.getenv("SESSION_SECRET", "")
if not secret:
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise RuntimeError("SESSION_SECRET must be set in production.")
    secret = "local-development-secret-change-before-deployment"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("The Merchant database is ready.")
    if not os.getenv("ADMIN_USERNAME") or not os.getenv("ADMIN_PASSWORD"):
        print("WARNING: Set admin credentials in .env.")
    yield


app = FastAPI(title="The Merchant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=secret,
    same_site="lax",
    https_only=os.getenv("ENVIRONMENT", "development").lower() == "production",
    max_age=28800,
)

app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    try:
        products = db.scalars(
            select(Product)
            .where(Product.is_active.is_(True), Product.stock > 0)
            .order_by(Product.created_at.desc())
        ).all()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"business_name": "The Merchant", "products": products},
        )
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "the-merchant-api",
        "database": "connected",
    }
