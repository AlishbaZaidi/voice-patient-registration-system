# Sets up the DB connection. Uses DATABASE_URL from the environment
# if present (Railway will provide this for Postgres), otherwise
# falls back to a local SQLite file for easy local testing.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base

DATABASE_URL= os.getenv("DATABASE_URL","sqlite:///./patients.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://","postgresql://",1)

connect_args = {"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency: gives each request its own DB session, and guarantees it's closed afterward even if an error occurs."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()