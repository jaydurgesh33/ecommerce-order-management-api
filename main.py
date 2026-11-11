from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
import auth
import jwt
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="E-Commerce Backend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except jwt.InvalidTokenError:
        raise credentials_error
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_error
    return user


def require_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@app.get("/")
def home():
    return {"message": "Backend working now!"}

@app.post("/categories", response_model=schemas.CategoryOut)
def create_category(
    data: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    existing = db.query(models.Category).filter(models.Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    category = models.Category(name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@app.get("/categories", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@app.post("/products", response_model=schemas.ProductOut)
def create_product(
    data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    category = db.get(models.Category, data.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    product = models.Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product



@app.get("/products", response_model=list[schemas.ProductOut])
def list_products(
    category_id: int = None,
    min_price:float = None,
    max_price:float = None,
    search:str=None,
    sort_order:str="asc",
    skip:int = 0,
    limit:int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)    #uvicorn main:app --reload

    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)

    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    if sort_order == "asc":
        query = query.order_by(models.Product.price.asc())
    else:
        query = query.order_by(models.Product.price.desc())

    return query.offset(skip).limit(limit).all()
    

@app.get("/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    data: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not db.get(models.Category, data.category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in data.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}

@app.post("/register", response_model=schemas.UserOut)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user = models.User(
        username=data.username,
        hashed_password=auth.hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = auth.create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}
@app.post("/orders", response_model=schemas.OrderOut)
def create_order(
    data: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        order = models.Order(user_id=current_user.id, status="placed", total_price=0)
        db.add(order)
        db.flush()

        total = 0
        for item in data.items:
            product = (
                db.query(models.Product)
                .filter(models.Product.id == item.product_id)
                .with_for_update()
                .first()
            )
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")
            product.stock -= item.quantity
            total += product.price * item.quantity
            db.add(
                models.OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    price=product.price,
                )
            )

        order.total_price = total
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not place order")

@app.get("/orders", response_model=list[schemas.OrderOut])
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.id.desc())
        .all()
    )