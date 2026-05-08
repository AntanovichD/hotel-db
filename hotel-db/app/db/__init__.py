"""Слой доступа к данным."""

from app.db.connection import Database
from app.db.repository import HotelRepository

__all__ = ["Database", "HotelRepository"]
