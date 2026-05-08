"""Обёртка над pyodbc-подключением."""
from __future__ import annotations

import contextlib
import locale
import platform
from typing import Any, Iterable, Iterator

import pyodbc

from app.config import DBConfig


class Database:
    """Лёгкая обёртка над pyodbc.Connection с автокоммитом."""

    def __init__(self, config: DBConfig) -> None:
        self._config = config
        self._conn: pyodbc.Connection | None = None

    def connect(self) -> None:
        if self._conn is not None:
            return
        if platform.system() == "Windows":
            char_enc = locale.getpreferredencoding(False) or "cp1251"
        else:
            char_enc = "utf-8"
        try:
            self._conn = pyodbc.connect(
                self._config.to_connection_string(), autocommit=True
            )
        except UnicodeDecodeError as ude:
            raw = getattr(ude, "object", b"")
            decoded = raw.decode(char_enc, errors="replace") if raw else "(пусто)"
            raise RuntimeError(
                "Не удалось подключиться к SQL Server. "
                "Текст ошибки от драйвера в локальной кодировке "
                f"({char_enc}):\n{decoded}\n\n"
                "Проверьте: HOTEL_DB_SERVER (имя инстанса), "
                "что база HOTEL_DB_NAME существует, что у пользователя есть доступ, "
                "что установлен ODBC Driver 18 for SQL Server."
            ) from ude
        # SQL_WCHAR (NVARCHAR/NCHAR) всегда UTF-16-LE — стандарт T-SQL.
        self._conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-16-le")
        # SQL_CHAR/ошибки: на Windows — системная ANSI (cp1251 на русской локали),
        # на Linux Microsoft-драйвер выдаёт UTF-8.
        self._conn.setdecoding(pyodbc.SQL_CHAR, encoding=char_enc)
        self._conn.setencoding(encoding="utf-16-le")

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    @contextlib.contextmanager
    def cursor(self) -> Iterator[pyodbc.Cursor]:
        if self._conn is None:
            self.connect()
        assert self._conn is not None
        cur = self._conn.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[pyodbc.Row]:
        with self.cursor() as cur:
            cur.execute(sql, *params) if params else cur.execute(sql)
            return cur.fetchall()

    def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> pyodbc.Row | None:
        with self.cursor() as cur:
            cur.execute(sql, *params) if params else cur.execute(sql)
            return cur.fetchone()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        with self.cursor() as cur:
            cur.execute(sql, *params) if params else cur.execute(sql)
            return cur.rowcount

    def call_proc(self, sql: str, params: Iterable[Any] = ()) -> list[pyodbc.Row]:
        """Вызвать хранимую процедуру через {CALL ...}."""
        with self.cursor() as cur:
            cur.execute(sql, *params) if params else cur.execute(sql)
            try:
                return cur.fetchall()
            except pyodbc.ProgrammingError:
                return []
