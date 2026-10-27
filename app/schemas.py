from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(default="General", min_length=1, max_length=100)
    description: str = Field(default="", max_length=5000)
    price: float = Field(ge=0, le=100000000)
    quantity: int = Field(default=0, ge=0, le=100000000)
    reorder_level: int = Field(default=5, ge=0, le=100000000)

    @field_validator("sku", "name", "category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=60)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    price: float | None = Field(default=None, ge=0, le=100000000)
    quantity: int | None = Field(default=None, ge=0, le=100000000)
    reorder_level: int | None = Field(default=None, ge=0, le=100000000)

class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StockAdjustment(BaseModel):
    change: int = Field(ge=-100000000, le=100000000)
    reason: str = Field(default="adjustment", min_length=1, max_length=40)
    note: str = Field(default="", max_length=300)

    @field_validator("change")
    @classmethod
    def change_cannot_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Stock change cannot be zero")
        return value

class StockMovementRead(BaseModel):
    id: int
    product_id: int
    change: int
    reason: str
    note: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DashboardRead(BaseModel):
    total_products: int
    total_units: int
    inventory_value: float
    low_stock_count: int
