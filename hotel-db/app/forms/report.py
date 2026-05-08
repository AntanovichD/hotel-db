"""Форма отчёта за период с экспортом в Word и печатью."""
from __future__ import annotations

import os
import platform
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from app.db.repository import HotelRepository
from app.forms.widgets import DataTable, LabeledCombo, LabeledEntry
from app.reports.word_export import export_period_report


def _parse_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ")


class ReportWindow(ctk.CTkToplevel):
    """Окно построения отчёта с фильтрами и экспортом в Word."""

    def __init__(self, master: ctk.CTk, repo: HotelRepository) -> None:
        super().__init__(master)
        self.title("Отчёт по работе гостиницы")
        self.geometry("1100x720")
        self.minsize(960, 600)
        self.repo = repo
        self._rows: list[dict[str, Any]] = []
        self._categories = repo.list_categories()
        self._employees = repo.list_employees()

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            container, text="Параметры отчёта", font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        params = ctk.CTkFrame(container)
        params.pack(fill="x")
        params.grid_columnconfigure((0, 1, 2, 3), weight=1)

        today = date.today()
        first_day = today.replace(day=1)
        self.start_date = LabeledEntry(params, "Дата с (ДД.ММ.ГГГГ)")
        self.start_date.set((first_day - timedelta(days=180)).strftime("%d.%m.%Y"))
        self.start_date.grid(row=0, column=0, padx=6, pady=4, sticky="ew")

        self.end_date = LabeledEntry(params, "Дата по")
        self.end_date.set((today + timedelta(days=365)).strftime("%d.%m.%Y"))
        self.end_date.grid(row=0, column=1, padx=6, pady=4, sticky="ew")

        self.category = LabeledCombo(
            params,
            "Категория",
            values=["— Все —"] + [c["CategoryName"] for c in self._categories],
        )
        self.category.set("— Все —")
        self.category.grid(row=0, column=2, padx=6, pady=4, sticky="ew")

        self.employee = LabeledCombo(
            params,
            "Сотрудник",
            values=["— Все —"] + [e["FullName"] for e in self._employees],
        )
        self.employee.set("— Все —")
        self.employee.grid(row=0, column=3, padx=6, pady=4, sticky="ew")

        # Кнопки
        btns = ctk.CTkFrame(container, fg_color="transparent")
        btns.pack(fill="x", pady=(8, 8))
        ctk.CTkButton(btns, text="Сформировать", command=self._on_run).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Экспорт в Word", command=self._on_export).pack(
            side="left", padx=4
        )
        ctk.CTkButton(btns, text="Печать", command=self._on_print).pack(side="left", padx=4)

        # Таблица результатов
        self.table = DataTable(
            container,
            columns=[
                ("RoomNumber", "№ номера", 100),
                ("CategoryName", "Категория", 130),
                ("GuestFullName", "Гость", 220),
                ("PassportNumber", "Паспорт", 110),
                ("EmployeeFullName", "Сотрудник", 200),
                ("CheckInDate", "Заселён", 140),
                ("ActualCheckOutDate", "Выселен", 140),
                ("Status", "Статус", 100),
                ("TotalCost", "Стоимость", 110),
            ],
            height=18,
        )
        self.table.pack(fill="both", expand=True, pady=(8, 8))

        # Сводная строка
        self.summary = ctk.CTkLabel(
            container, text="Записей: 0,  Сумма: 0.00 $,  Заполняемость: 0.00 %",
            font=("Segoe UI", 12, "bold"),
        )
        self.summary.pack(anchor="w", pady=(4, 0))

        self.transient(master)
        self.focus_set()

    # ------------------- логика -------------------
    def _read_params(self) -> tuple[date, date, int | None, int | None]:
        start = _parse_date(self.start_date.get())
        end = _parse_date(self.end_date.get())
        if end < start:
            raise ValueError("Дата 'по' меньше даты 'с'")

        cat_id: int | None = None
        if self.category.get() and self.category.get() != "— Все —":
            cat_id = next(
                (c["CategoryID"] for c in self._categories if c["CategoryName"] == self.category.get()),
                None,
            )
        emp_id: int | None = None
        if self.employee.get() and self.employee.get() != "— Все —":
            emp_id = next(
                (e["EmployeeID"] for e in self._employees if e["FullName"] == self.employee.get()),
                None,
            )
        return start, end, cat_id, emp_id

    def _on_run(self) -> None:
        try:
            start, end, cat_id, emp_id = self._read_params()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return
        try:
            rows = self.repo.get_period_report(start, end, cat_id, emp_id)
            occupancy = self.repo.get_occupancy_rate(start, end)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        self._rows = rows
        formatted = []
        total = 0.0
        for r in rows:
            row = dict(r)
            row["CheckInDate"] = HotelRepository.format_dt(row.get("CheckInDate"))
            row["ActualCheckOutDate"] = HotelRepository.format_dt(row.get("ActualCheckOutDate"))
            cost = float(row.get("TotalCost") or 0)
            total += cost
            row["TotalCost"] = f"{cost:.2f}"
            formatted.append(row)
        self.table.set_rows(formatted)
        self.summary.configure(
            text=(
                f"Записей: {len(rows)},  Сумма: {total:.2f} $,  "
                f"Заполняемость: {float(occupancy):.2f} %"
            )
        )

    def _on_export(self) -> None:
        if not self._rows:
            messagebox.showwarning("Внимание", "Сначала сформируйте отчёт.", parent=self)
            return
        try:
            start, end, _, _ = self._read_params()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return

        default_name = f"Отчёт_{start:%Y%m%d}_{end:%Y%m%d}.docx"
        default_dir = Path(__file__).resolve().parent.parent.parent / "exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".docx",
            filetypes=[("Документ Word", "*.docx")],
            initialdir=str(default_dir),
            initialfile=default_name,
        )
        if not path:
            return
        try:
            occupancy = self.repo.get_occupancy_rate(start, end)
            export_period_report(
                output_path=Path(path),
                rows=self._rows,
                start=start,
                end=end,
                category=self.category.get(),
                employee=self.employee.get(),
                occupancy=float(occupancy),
            )
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка экспорта", str(e), parent=self)
            return
        if messagebox.askyesno(
            "Готово", f"Отчёт сохранён в файл:\n{path}\n\nОткрыть его сейчас?", parent=self
        ):
            self._open_file(path)

    def _on_print(self) -> None:
        if not self._rows:
            messagebox.showwarning("Внимание", "Сначала сформируйте отчёт.", parent=self)
            return
        try:
            start, end, _, _ = self._read_params()
            occupancy = self.repo.get_occupancy_rate(start, end)
            tmp_dir = Path(__file__).resolve().parent.parent.parent / "exports"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / f"print_{start:%Y%m%d}_{end:%Y%m%d}.docx"
            export_period_report(
                output_path=tmp_path,
                rows=self._rows,
                start=start,
                end=end,
                category=self.category.get(),
                employee=self.employee.get(),
                occupancy=float(occupancy),
            )
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка печати", str(e), parent=self)
            return
        self._print_file(str(tmp_path))

    @staticmethod
    def _open_file(path: str) -> None:
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _print_file(path: str) -> None:
        system = platform.system()
        try:
            if system == "Windows":
                # ShellExecute "print" verb отправляет файл в принтер по умолчанию
                os.startfile(path, "print")  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.Popen(["lp", path])
            else:
                subprocess.Popen(["lp", path])
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка печати", str(e))
