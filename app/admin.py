
import hmac
import os
import secrets
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select

from app.database import SessionLocal
from app.models.product import Product

router = APIRouter(prefix="/admin", tags=["admin"])

ROOT = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(ROOT / "templates"))
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}


def authenticated(request: Request) -> bool:
    return request.session.get("admin_authenticated") is True


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def valid_csrf(request: Request, submitted: str) -> bool:
    expected = request.session.get("csrf_token", "")
    return bool(expected) and hmac.compare_digest(expected, submitted or "")


def login_redirect():
    return RedirectResponse("/admin/login", status_code=303)


def render(request, name, **context):
    return templates.TemplateResponse(
        request=request, name=name, context=context
    )


async def save_upload(upload: UploadFile | None, kind: str):
    if upload is None or not upload.filename:
        return None

    extension = Path(upload.filename).suffix.lower()
    allowed = IMAGE_EXTENSIONS if kind == "image" else VIDEO_EXTENSIONS
    maximum = 10 * 1024 * 1024 if kind == "image" else 100 * 1024 * 1024

    if extension not in allowed:
        raise ValueError(f"Unsupported {kind} file extension.")

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    total = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum:
                    raise ValueError(f"{kind.title()} exceeds the size limit.")
                output.write(chunk)

        if total == 0:
            raise ValueError("Uploaded file is empty.")

        if kind == "image":
            try:
                with Image.open(destination) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError):
                raise ValueError("The uploaded image is invalid.")

        return f"/media/{filename}"
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if authenticated(request):
        return RedirectResponse("/admin", status_code=303)
    return render(request, "admin_login.html", csrf_token=csrf_token(request),
                  error=None)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    submitted_csrf: str = Form(..., alias="csrf_token"),
):
    if not valid_csrf(request, submitted_csrf):
        return render(request, "admin_login.html",
                      csrf_token=csrf_token(request),
                      error="Session expired. Refresh and try again.")

    expected_user = os.getenv("ADMIN_USERNAME", "")
    expected_password = os.getenv("ADMIN_PASSWORD", "")

    user_ok = bool(expected_user) and hmac.compare_digest(
        username.encode(), expected_user.encode()
    )
    password_ok = bool(expected_password) and hmac.compare_digest(
        password.encode(), expected_password.encode()
    )

    if not (user_ok and password_ok):
        return HTMLResponse(
            content=templates.get_template("admin_login.html").render(
                request=request, csrf_token=csrf_token(request),
                error="Invalid username or password."
            ),
            status_code=401,
        )

    request.session.clear()
    request.session["admin_authenticated"] = True
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    return RedirectResponse("/admin", status_code=303)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    if valid_csrf(request, csrf_token):
        request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, message: str | None = None):
    if not authenticated(request):
        return login_redirect()

    db = SessionLocal()
    try:
        products = db.scalars(
            select(Product).order_by(Product.created_at.desc())
        ).all()
        return render(request, "admin_dashboard.html",
                      products=products, csrf_token=csrf_token(request),
                      message=message)
    finally:
        db.close()


@router.get("/products/new", response_class=HTMLResponse)
def new_product(request: Request):
    if not authenticated(request):
        return login_redirect()
    return render(request, "product_form.html", product=None,
                  csrf_token=csrf_token(request), error=None)


@router.post("/products")
async def create_product(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    price: str = Form(...),
    stock: int = Form(0),
    is_active: str | None = Form(None),
    csrf_token: str = Form(...),
    image: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
):
    if not authenticated(request):
        return login_redirect()
    if not valid_csrf(request, csrf_token):
        return HTMLResponse("Invalid CSRF token. Refresh the form.", status_code=403)

    try:
        amount = Decimal(price)
        if not amount.is_finite() or amount <= 0 or stock < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return render(request, "product_form.html", product=None,
                      csrf_token=csrf_token(request),
                      error="Enter a positive price and nonnegative stock.")

    saved_image = saved_video = None
    try:
        saved_image = await save_upload(image, "image")
        saved_video = await save_upload(video, "video")

        db = SessionLocal()
        try:
            product = Product(
                name=name.strip()[:160],
                category=category.strip()[:80],
                description=description.strip(),
                price=amount,
                stock=stock,
                image_path=saved_image,
                video_path=saved_video,
                is_active=is_active == "on",
            )
            if not product.name or not product.category:
                raise ValueError("Name and category are required.")
            db.add(product)
            db.commit()
        finally:
            db.close()
    except ValueError as exc:
        for path in (saved_image, saved_video):
            if path:
                (UPLOAD_DIR / Path(path).name).unlink(missing_ok=True)
        return render(request, "product_form.html", product=None,
                      csrf_token=csrf_token(request), error=str(exc))

    return RedirectResponse("/admin?message=Product%20created", status_code=303)
