"""Toplevel-окна справочников (категории, номера, гости, сотрудники, услуги)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox
from typing import Any, Callable

import customtkinter as ctk

from app.db.repository import HotelRepository
from app.forms.widgets import DataTable, LabeledCombo, LabeledEntry

# Словарь PK -> название колонки в репозитории
ROOM_STATUSES = ("Свободен", "Занят", "Ремонт")


def _parse_date(text: str) -> date | None:
    text = text.strip()
    if not text:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ")


def _parse_decimal(text: str) -> Decimal:
    text = text.strip().replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Ожидается число") from exc


class _DictionaryWindow(ctk.CTkToplevel):
    """Базовый класс окон-справочников с CRUD-функциональностью."""

    title_text = "Справочник"
    columns: list[tuple[str, str, int]] = []

    def __init__(
        self,
        master: ctk.CTk,
        repo: HotelRepository,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title(self.title_text)
        self.geometry("960x600")
        self.minsize(820, 480)
        self.repo = repo
        self.on_change = on_change
        self._current: dict[str, Any] | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)

        self.table = DataTable(container, self.columns, on_select=self._on_row_select, height=18)
        self.table.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.form = ctk.CTkFrame(container)
        self.form.grid(row=0, column=1, sticky="nsew")
        self._build_form(self.form)

        btn_frame = ctk.CTkFrame(self.form, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(8, 12))
        ctk.CTkButton(btn_frame, text="Добавить", command=self._on_add).pack(
            side="left", padx=4, expand=True, fill="x"
        )
        ctk.CTkButton(btn_frame, text="Изменить", command=self._on_update).pack(
            side="left", padx=4, expand=True, fill="x"
        )
        ctk.CTkButton(
            btn_frame,
            text="Удалить",
            fg_color="#a93226",
            hover_color="#7b241c",
            command=self._on_delete,
        ).pack(side="left", padx=4, expand=True, fill="x")

        ctk.CTkButton(
            self.form,
            text="Очистить",
            fg_color="transparent",
            border_width=1,
            border_color="#1f6aa5",
            text_color="#1f6aa5",
            hover_color="#e6f0f8",
            command=self._clear_form,
        ).pack(fill="x", padx=12, pady=(0, 12))

        self.refresh()
        self.transient(master)
        self.grab_set()
        self.focus_set()

    # Подкласс должен реализовать
    def _build_form(self, parent: ctk.CTkFrame) -> None:
        raise NotImplementedError

    def _read_form(self) -> dict[str, Any]:
        raise NotImplementedError

    def _fill_form(self, row: dict[str, Any]) -> None:
        raise NotImplementedError

    def _create(self, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def _update(self, data: dict[str, Any]) -> None:
        raise NotImplementedError

    def _delete(self, row: dict[str, Any]) -> None:
        raise NotImplementedError

    def _load_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _format_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return rows

    def _clear_form(self) -> None:
        self._current = None

    # Универсальная логика
    def refresh(self) -> None:
        rows = self._load_rows()
        self.table.set_rows(self._format_rows(rows))
        self._clear_form()
        if self.on_change:
            self.on_change()

    def _on_row_select(self, row: dict[str, Any] | None) -> None:
        if row is None:
            return
        self._current = row
        self._fill_form(row)

    def _on_add(self) -> None:
        try:
            data = self._read_form()
            self._create(data)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        self.refresh()

    def _on_update(self) -> None:
        if not self._current:
            messagebox.showwarning("Внимание", "Выберите запись для изменения.", parent=self)
            return
        try:
            data = self._read_form()
            self._update(data)
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        self.refresh()

    def _on_delete(self) -> None:
        if not self._current:
            messagebox.showwarning("Внимание", "Выберите запись для удаления.", parent=self)
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную запись?", parent=self):
            return
        try:
            self._delete(self._current)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        self.refresh()


# ---------------- Категории номеров ----------------
class CategoriesWindow(_DictionaryWindow):
    title_text = "Категории номеров"
    columns = [
        ("CategoryName", "Название", 200),
        ("BasePrice", "Цена за сутки", 140),
        ("Description", "Описание", 360),
    ]

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        self.name = LabeledEntry(parent, "Название")
        self.name.pack(fill="x", padx=12, pady=(12, 0))
        self.price = LabeledEntry(parent, "Цена за сутки")
        self.price.pack(fill="x", padx=12)
        self.descr = LabeledEntry(parent, "Описание")
        self.descr.pack(fill="x", padx=12)

    def _read_form(self) -> dict[str, Any]:
        name = self.name.get()
        if not name:
            raise ValueError("Введите название категории")
        return {
            "name": name,
            "base_price": _parse_decimal(self.price.get() or "0"),
            "description": self.descr.get() or None,
        }

    def _fill_form(self, row: dict[str, Any]) -> None:
        self.name.set(row.get("CategoryName"))
        self.price.set(row.get("BasePrice"))
        self.descr.set(row.get("Description"))

    def _create(self, data: dict[str, Any]) -> None:
        self.repo.add_category(**data)

    def _update(self, data: dict[str, Any]) -> None:
        assert self._current is not None
        self.repo.update_category(self._current["CategoryID"], **data)

    def _delete(self, row: dict[str, Any]) -> None:
        self.repo.delete_category(row["CategoryID"])

    def _load_rows(self) -> list[dict[str, Any]]:
        return self.repo.list_categories()

    def _clear_form(self) -> None:
        super()._clear_form()
        self.name.set("")
        self.price.set("")
        self.descr.set("")


# ---------------- Номера ----------------
class RoomsWindow(_DictionaryWindow):
    title_text = "Номера"
    columns = [
        ("RoomNumber", "№ номера", 100),
        ("CategoryName", "Категория", 160),
        ("Floor", "Этаж", 80),
        ("Status", "Статус", 120),
        ("CurrentGuest", "Текущий гость", 220),
        ("BasePrice", "Цена/сутки", 120),
    ]

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        self.number = LabeledEntry(parent, "№ номера")
        self.number.pack(fill="x", padx=12, pady=(12, 0))
        self.category = LabeledCombo(parent, "Категория")
        self.category.pack(fill="x", padx=12)
        self.floor = LabeledEntry(parent, "Этаж")
        self.floor.pack(fill="x", padx=12)
        self.status = LabeledCombo(parent, "Статус", values=ROOM_STATUSES)
        self.status.pack(fill="x", padx=12)
        self.notes = LabeledEntry(parent, "Примечание")
        self.notes.pack(fill="x", padx=12)
        self._categories: list[dict[str, Any]] = []

    def _refresh_categories(self) -> None:
        self._categories = self.repo.list_categories()
        self.category.configure_values([c["CategoryName"] for c in self._categories])

    def _read_form(self) -> dict[str, Any]:
        if not self.number.get():
            raise ValueError("Введите номер комнаты")
        if not self.category.get():
            raise ValueError("Выберите категорию")
        try:
            floor = int(self.floor.get() or "1")
        except ValueError as exc:
            raise ValueError("Этаж должен быть числом") from exc
        category = next(
            (c for c in self._categories if c["CategoryName"] == self.category.get()), None
        )
        if not category:
            raise ValueError("Категория не найдена в справочнике")
        return {
            "room_number": self.number.get(),
            "category_id": category["CategoryID"],
            "floor": floor,
            "status": self.status.get() or "Свободен",
            "notes": self.notes.get() or None,
        }

    def _fill_form(self, row: dict[str, Any]) -> None:
        self.number.set(row.get("RoomNumber"))
        self.category.set(row.get("CategoryName") or "")
        self.floor.set(row.get("Floor"))
        self.status.set(row.get("Status") or "Свободен")
        self.notes.set(self._fetch_room_notes(row["RoomID"]))

    def _fetch_room_notes(self, room_id: int) -> str:
        rows = self.repo.db.fetch_one("SELECT Notes FROM dbo.Rooms WHERE RoomID = ?", (room_id,))
        return rows[0] if rows and rows[0] else ""

    def _create(self, data: dict[str, Any]) -> None:
        self.repo.add_room(**data)

    def _update(self, data: dict[str, Any]) -> None:
        assert self._current is not None
        self.repo.update_room(self._current["RoomID"], **data)

    def _delete(self, row: dict[str, Any]) -> None:
        self.repo.delete_room(row["RoomID"])

    def _load_rows(self) -> list[dict[str, Any]]:
        self._refresh_categories()
        return self.repo.list_rooms()

    def _clear_form(self) -> None:
        super()._clear_form()
        self.number.set("")
        self.category.set("")
        self.floor.set("")
        self.status.set("Свободен")
        self.notes.set("")


# ---------------- Гости ----------------
class GuestsWindow(_DictionaryWindow):
    title_text = "Гости"
    columns = [
        ("FullName", "ФИО", 240),
        ("PassportNumber", "Паспорт", 120),
        ("BirthDate", "Дата рождения", 130),
        ("Phone", "Телефон", 140),
        ("Email", "Email", 200),
    ]

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        self.full_name = LabeledEntry(parent, "ФИО")
        self.full_name.pack(fill="x", padx=12, pady=(12, 0))
        self.passport = LabeledEntry(parent, "Паспорт")
        self.passport.pack(fill="x", padx=12)
        self.birth = LabeledEntry(parent, "Дата рожд. (ДД.ММ.ГГГГ)")
        self.birth.pack(fill="x", padx=12)
        self.phone = LabeledEntry(parent, "Телефон")
        self.phone.pack(fill="x", padx=12)
        self.email = LabeledEntry(parent, "Email")
        self.email.pack(fill="x", padx=12)

    def _read_form(self) -> dict[str, Any]:
        if not self.full_name.get():
            raise ValueError("Введите ФИО")
        if not self.passport.get():
            raise ValueError("Введите номер паспорта")
        return {
            "full_name": self.full_name.get(),
            "passport": self.passport.get(),
            "birth_date": _parse_date(self.birth.get()),
            "phone": self.phone.get() or None,
            "email": self.email.get() or None,
        }

    def _fill_form(self, row: dict[str, Any]) -> None:
        self.full_name.set(row.get("FullName"))
        self.passport.set(row.get("PassportNumber"))
        bd = row.get("BirthDate")
        self.birth.set(bd.strftime("%d.%m.%Y") if isinstance(bd, date) else "")
        self.phone.set(row.get("Phone"))
        self.email.set(row.get("Email"))

    def _format_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            r = dict(r)
            bd = r.get("BirthDate")
            r["BirthDate"] = bd.strftime("%d.%m.%Y") if isinstance(bd, date) else ""
            out.append(r)
        return out

    def _create(self, data: dict[str, Any]) -> None:
        self.repo.add_guest(**data)

    def _update(self, data: dict[str, Any]) -> None:
        assert self._current is not None
        self.repo.update_guest(self._current["GuestID"], **data)

    def _delete(self, row: dict[str, Any]) -> None:
        self.repo.delete_guest(row["GuestID"])

    def _load_rows(self) -> list[dict[str, Any]]:
        return self.repo.list_guests()

    def _clear_form(self) -> None:
        super()._clear_form()
        for w in (self.full_name, self.passport, self.birth, self.phone, self.email):
            w.set("")


# ---------------- Сотрудники ----------------
class EmployeesWindow(_DictionaryWindow):
    title_text = "Сотрудники"
    columns = [
        ("FullName", "ФИО", 220),
        ("Position", "Должность", 220),
        ("Phone", "Телефон", 140),
        ("HireDate", "Принят", 120),
    ]

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        self.full_name = LabeledEntry(parent, "ФИО")
        self.full_name.pack(fill="x", padx=12, pady=(12, 0))
        self.position = LabeledEntry(parent, "Должность")
        self.position.pack(fill="x", padx=12)
        self.phone = LabeledEntry(parent, "Телефон")
        self.phone.pack(fill="x", padx=12)
        self.hire = LabeledEntry(parent, "Дата приёма (ДД.ММ.ГГГГ)")
        self.hire.pack(fill="x", padx=12)

    def _read_form(self) -> dict[str, Any]:
        if not self.full_name.get():
            raise ValueError("Введите ФИО")
        if not self.position.get():
            raise ValueError("Введите должность")
        return {
            "full_name": self.full_name.get(),
            "position": self.position.get(),
            "phone": self.phone.get() or None,
            "hire_date": _parse_date(self.hire.get()),
        }

    def _fill_form(self, row: dict[str, Any]) -> None:
        self.full_name.set(row.get("FullName"))
        self.position.set(row.get("Position"))
        self.phone.set(row.get("Phone"))
        hd = row.get("HireDate")
        self.hire.set(hd.strftime("%d.%m.%Y") if isinstance(hd, date) else "")

    def _format_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            r = dict(r)
            hd = r.get("HireDate")
            r["HireDate"] = hd.strftime("%d.%m.%Y") if isinstance(hd, date) else ""
            out.append(r)
        return out

    def _create(self, data: dict[str, Any]) -> None:
        self.repo.add_employee(**data)

    def _update(self, data: dict[str, Any]) -> None:
        assert self._current is not None
        self.repo.update_employee(self._current["EmployeeID"], **data)

    def _delete(self, row: dict[str, Any]) -> None:
        self.repo.delete_employee(row["EmployeeID"])

    def _load_rows(self) -> list[dict[str, Any]]:
        return self.repo.list_employees()

    def _clear_form(self) -> None:
        super()._clear_form()
        for w in (self.full_name, self.position, self.phone, self.hire):
            w.set("")


# ---------------- Услуги ----------------
class ServicesWindow(_DictionaryWindow):
    title_text = "Дополнительные услуги"
    columns = [
        ("ServiceName", "Услуга", 220),
        ("Price", "Цена", 100),
        ("Description", "Описание", 360),
    ]

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        self.name = LabeledEntry(parent, "Название")
        self.name.pack(fill="x", padx=12, pady=(12, 0))
        self.price = LabeledEntry(parent, "Цена")
        self.price.pack(fill="x", padx=12)
        self.descr = LabeledEntry(parent, "Описание")
        self.descr.pack(fill="x", padx=12)

    def _read_form(self) -> dict[str, Any]:
        if not self.name.get():
            raise ValueError("Введите название услуги")
        return {
            "name": self.name.get(),
            "price": _parse_decimal(self.price.get() or "0"),
            "description": self.descr.get() or None,
        }

    def _fill_form(self, row: dict[str, Any]) -> None:
        self.name.set(row.get("ServiceName"))
        self.price.set(row.get("Price"))
        self.descr.set(row.get("Description"))

    def _create(self, data: dict[str, Any]) -> None:
        self.repo.add_service(**data)

    def _update(self, data: dict[str, Any]) -> None:
        assert self._current is not None
        self.repo.update_service(self._current["ServiceID"], **data)

    def _delete(self, row: dict[str, Any]) -> None:
        self.repo.delete_service(row["ServiceID"])

    def _load_rows(self) -> list[dict[str, Any]]:
        return self.repo.list_services()

    def _clear_form(self) -> None:
        super()._clear_form()
        for w in (self.name, self.price, self.descr):
            w.set("")
