"""Загрузка параметров подключения к MS SQL Server из .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback when dotenv не установлен
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False


@dataclass(frozen=True)
class DBConfig:
    server: str
    database: str
    driver: str
    user: str
    password: str
    trusted: bool
    trust_cert: bool

    def to_connection_string(self) -> str:
        parts: list[str] = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.trusted:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.user}")
            parts.append(f"PWD={self.password}")
        if self.trust_cert:
            parts.append("TrustServerCertificate=yes")
        parts.append("Encrypt=yes")
        return ";".join(parts)


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> DBConfig:
    """Прочитать .env (если есть) и вернуть DBConfig."""
    repo_root = Path(__file__).resolve().parent.parent
    env_file = repo_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    return DBConfig(
        server=os.getenv("HOTEL_DB_SERVER", "localhost"),
        database=os.getenv("HOTEL_DB_NAME", "HotelDB"),
        driver=os.getenv("HOTEL_DB_DRIVER", "ODBC Driver 18 for SQL Server"),
        user=os.getenv("HOTEL_DB_USER", "sa"),
        password=os.getenv("HOTEL_DB_PASSWORD", ""),
        trusted=_bool(os.getenv("HOTEL_DB_TRUSTED"), default=False),
        trust_cert=_bool(os.getenv("HOTEL_DB_TRUST_CERT"), default=True),
    )
