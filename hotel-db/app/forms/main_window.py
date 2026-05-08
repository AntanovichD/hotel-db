"""Главное окно — журнал заселений."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from app.db.repository import HotelRepository
from app.forms.checkin import CheckInWindow, CheckOutWindow
from app.forms.dictionaries import (
    CategoriesWindow,
    EmployeesWindow,
    GuestsWindow,
    RoomsWindow,
    ServicesWindow,
)
from app.forms.report import ReportWindow
from app.forms.widgets import DataTable


class MainWindow(ctk.CTk):
    """Главное окно приложения с журналом активных заселений."""

    def __init__(self, repo: HotelRepository) -> None:
        super().__init__()
        self.repo = repo
        self.title("Гостиница — учёт заселения и освобождения номеров")
        self.geometry("1280x760")
        self.minsize(1100, 660)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._build_menu()
        self._build_layout()

        self._show_active = True
        self.refresh()

    # ---------- меню ----------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Обновить", command=self.refresh, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        ops_menu = tk.Menu(menubar, tearoff=False)
        ops_menu.add_command(label="Заселить гостя", command=self._open_checkin)
        ops_menu.add_command(label="Выселить гостя", command=self._open_checkout)
        menubar.add_cascade(label="Операции", menu=ops_menu)

        ref_menu = tk.Menu(menubar, tearoff=False)
        ref_menu.add_command(label="Категории номеров", command=self._open_categories)
        ref_menu.add_command(label="Номера", command=self._open_rooms)
        ref_menu.add_command(label="Гости", command=self._open_guests)
        ref_menu.add_command(label="Сотрудники", command=self._open_employees)
        ref_menu.add_command(label="Дополнительные услуги", command=self._open_services)
        menubar.add_cascade(label="Справочники", menu=ref_menu)

        rep_menu = tk.Menu(menubar, tearoff=False)
        rep_menu.add_command(label="Отчёт за период", command=self._open_report)
        menubar.add_cascade(label="Отчёты", menu=rep_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="О программе", command=self._about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)
        self.bind("<F5>", lambda _e: self.refresh())

    # ---------- разметка ----------
    def _build_layout(self) -> None:
        toolbar = ctk.CTkFrame(self, height=56, corner_radius=0)
        toolbar.pack(fill="x")

        self.title_label = ctk.CTkLabel(
            toolbar,
            text="Журнал активных заселений",
            font=("Segoe UI", 18, "bold"),
        )
        self.title_label.pack(side="left", padx=16, pady=12)

        ctk.CTkButton(toolbar, text="Заселить", command=self._open_checkin, width=110).pack(
            side="right", padx=4, pady=10
        )
        ctk.CTkButton(toolbar, text="Выселить", command=self._open_checkout, width=110).pack(
            side="right", padx=4, pady=10
        )
        self.toggle_btn = ctk.CTkButton(
            toolbar,
            text="Показать всю историю",
            command=self._toggle_view,
            fg_color="transparent",
            border_width=1,
            border_color="#1f6aa5",
            text_color="#1f6aa5",
            hover_color="#e6f0f8",
            width=190,
        )
        self.toggle_btn.pack(side="right", padx=4, pady=10)

        # Поиск
        search_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        search_bar.pack(fill="x")
        ctk.CTkLabel(search_bar, text="Поиск (ФИО / паспорт / номер):").pack(
            side="left", padx=(16, 8), pady=8
        )
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(search_bar, textvariable=self.search_var, width=320)
        search_entry.pack(side="left", pady=8)
        search_entry.bind("<Return>", lambda _e: self.refresh())
        ctk.CTkButton(search_bar, text="Применить", command=self.refresh, width=110).pack(
            side="left", padx=8, pady=8
        )
        ctk.CTkButton(
            search_bar,
            text="Сброс",
            command=self._reset_search,
            fg_color="transparent",
            border_width=1,
            border_color="#1f6aa5",
            text_color="#1f6aa5",
            hover_color="#e6f0f8",
            width=80,
        ).pack(side="left", padx=4, pady=8)

        # Таблица журнала
        self.table = DataTable(
            self,
            columns=[
                ("StayID", "№", 60),
                ("RoomNumber", "Номер", 90),
                ("CategoryName", "Категория", 120),
                ("GuestFullName", "Гость", 220),
                ("PassportNumber", "Паспорт", 110),
                ("EmployeeFullName", "Администратор", 200),
                ("CheckInDate", "Заселён", 140),
                ("PlannedCheckOutDate", "Планируемое выселение", 170),
                ("ActualCheckOutDate", "Фактическое выселение", 170),
                ("Status", "Статус", 110),
                ("TotalCost", "Стоимость", 110),
            ],
            on_double_click=self._on_row_double,
            height=22,
        )
        self.table.pack(fill="both", expand=True, padx=12, pady=8)

        # Статусная строка
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            font=("Segoe UI", 11),
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 8))

    # ---------- логика ----------
    def refresh(self) -> None:
        try:
            if self._show_active:
                rows = self.repo.list_active_stays()
                search = self.search_var.get().strip().lower()
                if search:
                    rows = [
                        r
                        for r in rows
                        if search in (r.get("GuestFullName") or "").lower()
                        or search in (r.get("PassportNumber") or "").lower()
                        or search in (r.get("RoomNumber") or "").lower()
                        or search in (r.get("EmployeeFullName") or "").lower()
                    ]
                self.title_label.configure(text="Журнал активных заселений")
                self.toggle_btn.configure(text="Показать всю историю")
            else:
                rows = self.repo.list_all_stays(self.search_var.get() or None)
                self.title_label.configure(text="История всех заселений")
                self.toggle_btn.configure(text="Только активные")
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        formatted: list[dict[str, Any]] = []
        for r in rows:
            row = dict(r)
            row["CheckInDate"] = HotelRepository.format_dt(row.get("CheckInDate"))
            row["PlannedCheckOutDate"] = HotelRepository.format_dt(row.get("PlannedCheckOutDate"))
            row["ActualCheckOutDate"] = HotelRepository.format_dt(row.get("ActualCheckOutDate"))
            cost = row.get("TotalCost")
            row["TotalCost"] = f"{float(cost):.2f}" if cost is not None else ""
            row["Status"] = row.get("Status") or ("Активно" if not row["ActualCheckOutDate"] else "Завершено")
            formatted.append(row)

        self.table.set_rows(formatted)
        self.status_label.configure(text=f"Записей в журнале: {len(formatted)}")

    def _toggle_view(self) -> None:
        self._show_active = not self._show_active
        self.refresh()

    def _reset_search(self) -> None:
        self.search_var.set("")
        self.refresh()

    def _on_row_double(self, row: dict[str, Any]) -> None:
        if not row.get("ActualCheckOutDate"):
            self._open_checkout_for(row)

    def _open_checkin(self) -> None:
        CheckInWindow(self, self.repo, on_done=self.refresh)

    def _open_checkout(self) -> None:
        row = self.table.selected_row()
        if not row:
            messagebox.showinfo(
                "Подсказка",
                "Выберите активное заселение в таблице (двойной клик тоже сработает).",
                parent=self,
            )
            return
        if row.get("ActualCheckOutDate"):
            messagebox.showwarning(
                "Внимание", "Это заселение уже завершено.", parent=self
            )
            return
        self._open_checkout_for(row)

    def _open_checkout_for(self, row: dict[str, Any]) -> None:
        try:
            stay = self.repo.get_stay(int(row["StayID"]))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        if stay is None:
            messagebox.showerror("Ошибка", "Запись не найдена.", parent=self)
            return
        CheckOutWindow(self, self.repo, stay, on_done=self.refresh)

    def _open_categories(self) -> None:
        CategoriesWindow(self, self.repo, on_change=self.refresh)

    def _open_rooms(self) -> None:
        RoomsWindow(self, self.repo, on_change=self.refresh)

    def _open_guests(self) -> None:
        GuestsWindow(self, self.repo, on_change=self.refresh)

    def _open_employees(self) -> None:
        EmployeesWindow(self, self.repo, on_change=self.refresh)

    def _open_services(self) -> None:
        ServicesWindow(self, self.repo, on_change=self.refresh)

    def _open_report(self) -> None:
        ReportWindow(self, self.repo)

    def _about(self) -> None:
        messagebox.showinfo(
            "О программе",
            "Информационная система «Гостиница»\n"
            "Учёт заселения и освобождения номеров\n\n"
            "Курсовая работа.\n"
            "Python 3.11 · customtkinter · pyodbc · MS SQL Server",
            parent=self,
        )
