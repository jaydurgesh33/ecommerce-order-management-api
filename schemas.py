from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str

class CategoryOut(CategoryCreate):
    id: int
    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category_id: int


class ProductOut(ProductCreate):
    id: int
    model_config = {"from_attributes": True}

class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: float
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    status: str
    total_price: float
    items: list[OrderItemOut]
    model_config = {"from_attributes": True}
    