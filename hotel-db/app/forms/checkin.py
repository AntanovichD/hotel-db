"""Окна заселения и выселения гостя."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from tkinter import messagebox
from typing import Any, Callable

import customtkinter as ctk

from app.db.repository import HotelRepository
from app.forms.widgets import DataTable, LabeledCombo, LabeledEntry


def _parse_date(text: str) -> date:
    text = text.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ")


class CheckInWindow(ctk.CTkToplevel):
    """Форма заселения нового гостя."""

    def __init__(
        self,
        master: ctk.CTk,
        repo: HotelRepository,
        on_done: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title("Заселение гостя")
        self.geometry("520x460")
        self.minsize(480, 460)
        self.resizable(False, False)
        self.repo = repo
        self.on_done = on_done

        self._rooms = repo.list_free_rooms()
        self._guests = repo.list_guests()
        self._employees = repo.list_employees()

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            container, text="Регистрация заселения", font=("Segoe UI", 16, "bold")
        ).pack(pady=(4, 12))

        self.room = LabeledCombo(
            container,
            "Свободный номер",
            values=[
                f"{r['RoomNumber']} ({r['CategoryName']}, {r['BasePrice']:.2f}$/сутки)"
                for r in self._rooms
            ],
        )
        self.room.pack(fill="x", pady=4)

        self.guest = LabeledCombo(
            container,
            "Гость",
            values=[f"{g['FullName']} ({g['PassportNumber']})" for g in self._guests],
        )
        self.guest.pack(fill="x", pady=4)

        self.employee = LabeledCombo(
            container,
            "Администратор",
            values=[f"{e['FullName']} ({e['Position']})" for e in self._employees],
        )
        self.employee.pack(fill="x", pady=4)

        default_checkout = (date.today() + timedelta(days=1)).strftime("%d.%m.%Y")
        self.checkout_date = LabeledEntry(container, "Плановая дата выселения")
        self.checkout_date.pack(fill="x", pady=4)
        self.checkout_date.set(default_checkout)

        self.notes = LabeledEntry(container, "Примечание")
        self.notes.pack(fill="x", pady=4)

        btns = ctk.CTkFrame(container, fg_color="transparent")
        btns.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(btns, text="Заселить", command=self._on_confirm).pack(
            side="left", padx=4, expand=True, fill="x"
        )
        ctk.CTkButton(
            btns,
            text="Отмена",
            fg_color="transparent",
            border_width=1,
            border_color="#1f6aa5",
            text_color="#1f6aa5",
            hover_color="#e6f0f8",
            command=self.destroy,
        ).pack(side="left", padx=4, expand=True, fill="x")

        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _on_confirm(self) -> None:
        try:
            if not self.room.get() or not self._rooms:
                raise ValueError("Выберите свободный номер")
            if not self.guest.get():
                raise ValueError("Выберите гостя")
            if not self.employee.get():
                raise ValueError("Выберите администратора")

            room_idx = next(
                i
                for i, r in enumerate(self._rooms)
                if self.room.get().startswith(f"{r['RoomNumber']} ")
            )
            guest_idx = next(
                i
                for i, g in enumerate(self._guests)
                if self.guest.get() == f"{g['FullName']} ({g['PassportNumber']})"
            )
            emp_idx = next(
                i
                for i, e in enumerate(self._employees)
                if self.employee.get() == f"{e['FullName']} ({e['Position']})"
            )
            checkout = _parse_date(self.checkout_date.get())

            self.repo.check_in_guest(
                room_id=self._rooms[room_idx]["RoomID"],
                guest_id=self._guests[guest_idx]["GuestID"],
                employee_id=self._employees[emp_idx]["EmployeeID"],
                planned_checkout=checkout,
                notes=self.notes.get() or None,
            )
        except StopIteration:
            messagebox.showerror("Ошибка", "Не удалось определить запись.", parent=self)
            return
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            return
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return

        messagebox.showinfo("Готово", "Гость успешно заселён.", parent=self)
        if self.on_done:
            self.on_done()
        self.destroy()


class CheckOutWindow(ctk.CTkToplevel):
    """Форма выселения с расчётом итоговой стоимости и добавлением услуг."""

    def __init__(
        self,
        master: ctk.CTk,
        repo: HotelRepository,
        stay: dict[str, Any],
        on_done: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title(f"Выселение — {stay.get('GuestFullName')}")
        self.geometry("780x600")
        self.minsize(720, 560)
        self.repo = repo
        self.stay = stay
        self.on_done = on_done
        self._services = repo.list_services()

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        info = ctk.CTkFrame(container, fg_color=("#f0f0f0", "#1e1e1e"))
        info.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            info,
            text=(
                f"Гость:  {stay.get('GuestFullName')}\n"
                f"Номер:  {stay.get('RoomNumber')} — {stay.get('CategoryName')}\n"
                f"Заселён: {HotelRepository.format_dt(stay.get('CheckInDate'))}\n"
                f"План. выселение: {HotelRepository.format_dt(stay.get('PlannedCheckOutDate'))}"
            ),
            justify="left",
            anchor="w",
            font=("Segoe UI", 12),
        ).pack(fill="x", padx=12, pady=8)

        # Блок добавления услуг
        services_block = ctk.CTkFrame(container)
        services_block.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            services_block, text="Дополнительные услуги", font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 4))

        add_row = ctk.CTkFrame(services_block, fg_color="transparent")
        add_row.pack(fill="x", padx=12)
        self.service_combo = LabeledCombo(
            add_row,
            "Услуга",
            values=[f"{s['ServiceName']} ({s['Price']:.2f}$)" for s in self._services],
        )
        self.service_combo.pack(side="left", expand=True, fill="x", padx=(0, 8))
        self.qty = LabeledEntry(add_row, "Кол-во", width=80)
        self.qty.pack(side="left", padx=(0, 8))
        self.qty.set("1")
        ctk.CTkButton(add_row, text="Добавить", command=self._on_add_service, width=100).pack(
            side="left", pady=(20, 0)
        )

        self.services_table = DataTable(
            services_block,
            columns=[
                ("ServiceName", "Услуга", 200),
                ("ServiceDate", "Дата", 140),
                ("Quantity", "Кол-во", 80),
                ("Cost", "Цена", 100),
            ],
            height=6,
        )
        self.services_table.pack(fill="x", padx=12, pady=(8, 12))

        # Кнопки
        btns = ctk.CTkFrame(container, fg_color="transparent")
        btns.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            btns,
            text="Выселить и рассчитать стоимость",
            command=self._on_checkout,
            fg_color="#27ae60",
            hover_color="#1e8449",
        ).pack(side="left", padx=4, expand=True, fill="x")
        ctk.CTkButton(
            btns,
            text="Закрыть",
            fg_color="transparent",
            border_width=1,
            border_color="#1f6aa5",
            text_color="#1f6aa5",
            hover_color="#e6f0f8",
            command=self.destroy,
        ).pack(side="left", padx=4, expand=True, fill="x")

        self._refresh_services()
        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _refresh_services(self) -> None:
        rows = self.repo.list_stay_services(self.stay["StayID"])
        for r in rows:
            r["ServiceDate"] = HotelRepository.format_dt(r.get("ServiceDate"))
            r["Cost"] = f"{r['Cost']:.2f}"
        self.services_table.set_rows(rows)

    def _on_add_service(self) -> None:
        if not self.service_combo.get():
            messagebox.showwarning("Внимание", "Выберите услугу.", parent=self)
            return
        try:
            qty = int(self.qty.get() or "1")
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть положительным числом.", parent=self)
            return
        try:
            service = next(
                s
                for s in self._services
                if self.service_combo.get() == f"{s['ServiceName']} ({s['Price']:.2f}$)"
            )
        except StopIteration:
            messagebox.showerror("Ошибка", "Услуга не найдена.", parent=self)
            return
        try:
            self.repo.add_stay_service(self.stay["StayID"], service["ServiceID"], qty)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        self._refresh_services()

    def _on_checkout(self) -> None:
        if not messagebox.askyesno(
            "Подтверждение", "Оформить выселение и рассчитать стоимость?", parent=self
        ):
            return
        try:
            total = self.repo.check_out_guest(self.stay["StayID"])
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка БД", str(e), parent=self)
            return
        messagebox.showinfo(
            "Выселение оформлено",
            f"Итоговая стоимость: {total:.2f}$",
            parent=self,
        )
        if self.on_done:
            self.on_done()
        self.destroy()
