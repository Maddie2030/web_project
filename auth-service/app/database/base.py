# app/database/base.py

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all your models here so Alembic sees them
from app.models import user  # noqa
