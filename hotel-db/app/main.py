"""Точка входа в приложение «Гостиница»."""
from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from app.config import load_config
from app.db import Database, HotelRepository
from app.forms.main_window import MainWindow


def _show_connection_error(error: Exception) -> None:
    """Показать понятное сообщение об ошибке подключения."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Не удалось подключиться к БД",
        "Проверьте параметры в файле .env и доступность SQL Server.\n\n"
        f"Текст ошибки:\n{error}",
    )
    root.destroy()


def main() -> int:
    config = load_config()
    db = Database(config)
    try:
        db.connect()
    except Exception as exc:  # noqa: BLE001
        _show_connection_error(exc)
        return 1

    repo = HotelRepository(db)
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = MainWindow(repo)
    try:
        app.mainloop()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
