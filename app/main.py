from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pathlib import Path

from .database import Base, engine, get_db
from .models import Product, StockMovement
from .schemas import (
    DashboardRead, ProductCreate, ProductRead, ProductUpdate,
    StockAdjustment, StockMovementRead,
)

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for a starter project. Use Alembic migrations for production.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Inventory Management API",
    description="A portfolio project for managing products, stock, and inventory metrics.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/products", response_model=list[ProductRead])
def list_products(
    search: str | None = Query(default=None, max_length=160),
    category: str | None = Query(default=None, max_length=100),
    low_stock: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Product)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(or_(Product.name.ilike(term), Product.sku.ilike(term), Product.category.ilike(term)))
    if category:
        stmt = stmt.where(Product.category == category.strip())
    if low_stock:
        stmt = stmt.where(Product.quantity <= Product.reorder_level)
    stmt = stmt.order_by(Product.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())

@app.post("/api/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this SKU already exists.")
    if product.quantity:
        db.add(StockMovement(product_id=product.id, change=product.quantity, reason="initial_stock", note="Opening stock"))
        db.commit()
    return product

@app.get("/api/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

@app.patch("/api/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    changes = payload.model_dump(exclude_unset=True)
    # Stock changes should use the stock-adjustment endpoint to preserve an audit trail.
    if "quantity" in changes:
        raise HTTPException(status_code=400, detail="Use the stock adjustment endpoint to change quantity.")
    for key, value in changes.items():
        if value is not None:
            setattr(product, key, value)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this SKU already exists.")
    return product

@app.delete("/api/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.delete(product)
    db.commit()
    return None

@app.post("/api/products/{product_id}/stock", response_model=StockMovementRead, status_code=201)
def adjust_stock(product_id: int, payload: StockAdjustment, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    new_quantity = product.quantity + payload.change
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock: quantity cannot become negative.")
    product.quantity = new_quantity
    movement = StockMovement(
        product_id=product.id,
        change=payload.change,
        reason=payload.reason.strip(),
        note=payload.note.strip(),
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement

@app.get("/api/products/{product_id}/movements", response_model=list[StockMovementRead])
def product_movements(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found.")
    stmt = select(StockMovement).where(StockMovement.product_id == product_id).order_by(StockMovement.id.desc())
    return list(db.scalars(stmt).all())

@app.get("/api/dashboard", response_model=DashboardRead)
def dashboard(db: Session = Depends(get_db)):
    total_products = db.scalar(select(func.count(Product.id))) or 0
    total_units = db.scalar(select(func.coalesce(func.sum(Product.quantity), 0))) or 0
    inventory_value = db.scalar(select(func.coalesce(func.sum(Product.price * Product.quantity), 0.0))) or 0.0
    low_stock_count = db.scalar(select(func.count(Product.id)).where(Product.quantity <= Product.reorder_level)) or 0
    return DashboardRead(
        total_products=total_products,
        total_units=total_units,
        inventory_value=round(float(inventory_value), 2),
        low_stock_count=low_stock_count,
    )

@app.get("/api/categories", response_model=list[str])
def categories(db: Session = Depends(get_db)):
    stmt = select(Product.category).distinct().order_by(Product.category)
    return list(db.scalars(stmt).all())
