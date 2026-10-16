
import os
import re
import hmac
import hashlib
import secrets
import json
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

from app.database import init_db, get_db

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-only-change-this-secret"
)
ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    "admin@themerchant.co.ke"
).strip().lower()
ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "ChangeThisAdminPassword123!"
)

app = FastAPI(title="The Merchant")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=os.getenv("COOKIE_HTTPS_ONLY", "false").lower() == "true",
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 310000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 310000
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, AttributeError):
        return False


def current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    with get_db() as db:
        user = db.execute(
            "SELECT id, name, email, role, referral_code "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if not user:
        request.session.clear()
        return None
    return dict(user)


def page(request: Request, template: str, **context):
    context["request"] = request
    context["user"] = current_user(request)
    context["message"] = request.query_params.get("message")
    return templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
    )


@app.on_event("startup")
def startup():
    init_db()

    # Bootstrap the admin account from environment variables.
    with get_db() as db:
        admin = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (ADMIN_EMAIL,),
        ).fetchone()

        if not admin:
            db.execute("""
                INSERT INTO users
                (name, email, password_hash, role, referral_code)
                VALUES (?, ?, ?, 'admin', ?)
            """, (
                "The Merchant Admin",
                ADMIN_EMAIL,
                hash_password(ADMIN_PASSWORD),
                "ADMIN" + secrets.token_hex(4).upper(),
            ))


@app.get("/", response_class=HTMLResponse)
def storefront(request: Request):
    category = request.query_params.get("category", "all")
    search = request.query_params.get("q", "").strip()

    sql = "SELECT * FROM products WHERE active = 1"
    params = []

    if category.lower() != "all":
        sql += " AND category = ?"
        params.append(category)

    if search:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY id DESC"

    with get_db() as db:
        products = [
            dict(row) for row in db.execute(sql, params).fetchall()
        ]
        categories = [
            row["category"] for row in db.execute(
                "SELECT DISTINCT category FROM products "
                "WHERE active = 1 ORDER BY category"
            ).fetchall()
        ]

    return page(
        request,
        "index.html",
        products=products,
        categories=categories,
        selected_category=category,
        search=search,
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if current_user(request):
        return RedirectResponse("/dashboard", status_code=303)

    return page(request, "register.html")


@app.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    referral: str = Form(""),
):
    name = name.strip()
    email = email.strip().lower()
    referral = referral.strip().upper()

    if len(name) < 2 or len(name) > 100:
        return RedirectResponse(
            "/register?message=Enter+a+valid+name",
            status_code=303,
        )

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return RedirectResponse(
            "/register?message=Enter+a+valid+email",
            status_code=303,
        )

    if len(password) < 10:
        return RedirectResponse(
            "/register?message=Password+must+be+at+least+10+characters",
            status_code=303,
        )

    with get_db() as db:
        if db.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone():
            return RedirectResponse(
                "/register?message=Email+already+registered",
                status_code=303,
            )

        referrer = None
        if referral:
            referrer = db.execute(
                "SELECT id FROM users WHERE referral_code = ? AND role = 'customer'",
                (referral,),
            ).fetchone()

        referral_code = "TM" + secrets.token_hex(5).upper()

        cursor = db.execute("""
            INSERT INTO users
            (name, email, password_hash, role, referral_code, referred_by)
            VALUES (?, ?, ?, 'customer', ?, ?)
        """, (
            name,
            email,
            hash_password(password),
            referral_code,
            referrer["id"] if referrer else None,
        ))

        new_user_id = cursor.lastrowid

        if referrer:
            db.execute("""
                INSERT INTO referrals
                (referrer_id, referred_user_id)
                VALUES (?, ?)
            """, (referrer["id"], new_user_id))

    request.session.clear()
    request.session["user_id"] = new_user_id
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/dashboard", status_code=303)
    return page(request, "login.html")


@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    with get_db() as db:
        user = db.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse(
            "/login?message=Invalid+email+or+password",
            status_code=303,
        )

    request.session.clear()
    request.session["user_id"] = user["id"]
    return RedirectResponse("/dashboard", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def customer_dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user["role"] == "admin":
        return RedirectResponse("/admin", status_code=303)

    with get_db() as db:
        orders = [
            dict(row) for row in db.execute("""
                SELECT id, total, status, created_at
                FROM orders WHERE user_id = ?
                ORDER BY id DESC
            """, (user["id"],)).fetchall()
        ]

        referrals = [
            dict(row) for row in db.execute("""
                SELECT u.name, r.status, r.created_at
                FROM referrals r
                JOIN users u ON u.id = r.referred_user_id
                WHERE r.referrer_id = ?
                ORDER BY r.id DESC
            """, (user["id"],)).fetchall()
        ]

    referral_url = str(request.base_url).rstrip("/") + (
        "/register?ref=" + quote(user["referral_code"])
    )

    return page(
        request,
        "customer_dashboard.html",
        orders=orders,
        referrals=referrals,
        referral_url=referral_url,
    )


@app.post("/checkout")
async def checkout(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user["role"] != "customer":
        return RedirectResponse("/admin", status_code=303)

    form = await request.form()
    try:
        cart = json.loads(str(form.get("cart", "[]")))
    except json.JSONDecodeError:
        cart = []

    if not isinstance(cart, list) or not cart or len(cart) > 100:
        return RedirectResponse(
            "/?message=Your+cart+is+empty+or+invalid",
            status_code=303,
        )

    quantities = {}
    for item in cart:
        if not isinstance(item, dict):
            continue
        try:
            product_id = int(item.get("id"))
            quantity = int(item.get("quantity"))
        except (ValueError, TypeError):
            continue
        if product_id > 0 and 1 <= quantity <= 50:
            quantities[product_id] = min(
                50, quantities.get(product_id, 0) + quantity
            )

    if not quantities:
        return RedirectResponse(
            "/?message=Your+cart+is+empty",
            status_code=303,
        )

    with get_db() as db:
        ids = list(quantities)
        placeholders = ",".join("?" for _ in ids)
        products = db.execute(
            f"SELECT id, price, stock FROM products "
            f"WHERE active = 1 AND id IN ({placeholders})",
            ids,
        ).fetchall()
        by_id = {row["id"]: row for row in products}

        if len(by_id) != len(quantities):
            return RedirectResponse(
                "/?message=One+or+more+products+are+unavailable",
                status_code=303,
            )

        total = 0.0
        for product_id, quantity in quantities.items():
            product = by_id[product_id]
            if product["stock"] < quantity:
                return RedirectResponse(
                    "/?message=Insufficient+stock+for+a+cart+item",
                    status_code=303,
                )
            total += product["price"] * quantity

        cursor = db.execute(
            "INSERT INTO orders (user_id, total) VALUES (?, ?)",
            (user["id"], round(total, 2)),
        )
        order_id = cursor.lastrowid

        for product_id, quantity in quantities.items():
            product = by_id[product_id]
            db.execute("""
                INSERT INTO order_items
                (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (
                order_id,
                product_id,
                quantity,
                product["price"],
            ))
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (quantity, product_id),
            )

    # This records an order; it does not charge a payment method.
    return RedirectResponse(
        "/dashboard?message=Order+placed+successfully",
        status_code=303,
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")

    with get_db() as db:
        products = [
            dict(row) for row in db.execute(
                "SELECT * FROM products ORDER BY id DESC"
            ).fetchall()
        ]

        orders = [
            dict(row) for row in db.execute("""
                SELECT o.id, o.total, o.status, o.created_at, u.name, u.email
                FROM orders o JOIN users u ON u.id = o.user_id
                ORDER BY o.id DESC LIMIT 100
            """).fetchall()
        ]

        customers = [
            dict(row) for row in db.execute("""
                SELECT id, name, email, referral_code, created_at
                FROM users WHERE role = 'customer'
                ORDER BY id DESC LIMIT 200
            """).fetchall()
        ]

        referral_count = db.execute(
            "SELECT COUNT(*) AS n FROM referrals"
        ).fetchone()["n"]

        order_count = db.execute(
            "SELECT COUNT(*) AS n FROM orders"
        ).fetchone()["n"]

        customer_count = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'customer'"
        ).fetchone()["n"]

    return page(
        request,
        "admin_dashboard.html",
        products=products,
        orders=orders,
        customers=customers,
        referral_count=referral_count,
        order_count=order_count,
        customer_count=customer_count,
    )


@app.post("/admin/products")
def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("General"),
    price: float = Form(...),
    image_url: str = Form(""),
    stock: int = Form(0),
):
    user = current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")

    name = name.strip()
    category = category.strip() or "General"
    image_url = image_url.strip()

    if not name or len(name) > 150 or price < 0 or stock < 0:
        raise HTTPException(status_code=400, detail="Invalid product details")

    if image_url and not image_url.startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="Image URL must use HTTP or HTTPS")

    with get_db() as db:
        db.execute("""
            INSERT INTO products
            (name, description, category, price, image_url, stock)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            description.strip(),
            category,
            round(price, 2),
            image_url,
            stock,
        ))

    return RedirectResponse("/admin?message=Product+added", status_code=303)


@app.post("/admin/products/{product_id}/toggle")
def toggle_product(request: Request, product_id: int):
    user = current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")

    with get_db() as db:
        db.execute("""
            UPDATE products SET active = CASE active
                WHEN 1 THEN 0 ELSE 1 END
            WHERE id = ?
        """, (product_id,))

    return RedirectResponse("/admin?message=Product+updated", status_code=303)


@app.post("/admin/orders/{order_id}/status")
def update_order_status(
    request: Request,
    order_id: int,
    status: str = Form(...),
):
    user = current_user(request)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")

    allowed = {"Pending", "Confirmed", "Processing", "Shipped", "Completed", "Cancelled"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid order status")

    with get_db() as db:
        existing = db.execute(
            "SELECT status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Order not found")

        # Stock restoration on cancellation is deliberately not automated here.
        db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )

    return RedirectResponse("/admin?message=Order+status+updated", status_code=303)
