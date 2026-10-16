
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

PROJECT_ROOT = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "templates"))

router = APIRouter(tags=["dashboard-pages"])


@router.get("/dashboard/customer", name="customer_dashboard")
async def customer_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="customer_dashboard.html",
        context={},
    )


@router.get("/dashboard/admin", name="admin_dashboard")
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={},
    )
