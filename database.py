import os
import ssl
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file")

# Azure MySQL requires SSL. Enabled only when DB_SSL=true (set on Azure, not locally).
connect_args = {}
if os.getenv("DB_SSL", "false").lower() == "true":
    connect_args["ssl"] = ssl.create_default_context()

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()