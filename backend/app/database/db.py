from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import (
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_NAME
)

DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:"
    f"{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:"
    f"{DATABASE_PORT}/"
    f"{DATABASE_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
