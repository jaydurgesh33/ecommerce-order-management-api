# E-Commerce Order Management API

Backend REST API built with FastAPI and MySQL for managing categories, products and customer orders, with JWT authentication.

## Features
- User registration and login with JWT tokens (Argon2 password hashing)
- Category and product CRUD (create/update/delete restricted to admin)
- Product search, filter (category, price range), sort and pagination
- Order placement with transaction handling and automatic stock rollback on failure
- View my orders (authenticated)

## Tech Stack
Python, FastAPI, SQLAlchemy, MySQL (PyMySQL), JWT (PyJWT), pwdlib (Argon2), python-dotenv

## Setup
1. Clone the repo and create a virtual environment:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a MySQL database named `ecommerce_db`.

3. Copy `.env.example` to `.env` and fill in your values:

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/ecommerce_db
SECRET_KEY=your-long-random-string
```

4. Run the server:

```
uvicorn main:app --reload
```

5. Open http://127.0.0.1:8000/docs for the interactive Swagger UI.

## Main Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /register | Register a new user |
| POST | /login | Login and get JWT token |
| GET | /categories | List categories |
| POST | /categories | Create category (admin) |
| GET | /products | List products with filters |
| POST | /products | Create product (admin) |
| POST | /orders | Place an order |
| GET | /orders | List my orders |

## Author
Durgesh Jayswal