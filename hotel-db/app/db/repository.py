"""Высокоуровневый репозиторий для работы со всеми сущностями БД."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pyodbc

from app.db.connection import Database


def _row_to_dict(cursor: pyodbc.Cursor, row: pyodbc.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    columns = [c[0] for c in cursor.description]
    return dict(zip(columns, row, strict=False))


def _rows_to_dicts(cursor: pyodbc.Cursor, rows: list[pyodbc.Row]) -> list[dict[str, Any]]:
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, r, strict=False)) for r in rows]


class HotelRepository:
    """Все запросы к БД проходят через этот класс."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # ---------- Категории номеров ----------
    def list_categories(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT CategoryID, CategoryName, BasePrice, Description "
                "FROM dbo.RoomCategories ORDER BY CategoryName"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def add_category(self, name: str, base_price: Decimal, description: str | None) -> None:
        self.db.execute(
            "INSERT INTO dbo.RoomCategories (CategoryName, BasePrice, Description) VALUES (?, ?, ?)",
            (name, base_price, description),
        )

    def update_category(
        self, category_id: int, name: str, base_price: Decimal, description: str | None
    ) -> None:
        self.db.execute(
            "UPDATE dbo.RoomCategories "
            "SET CategoryName = ?, BasePrice = ?, Description = ? WHERE CategoryID = ?",
            (name, base_price, description, category_id),
        )

    def delete_category(self, category_id: int) -> None:
        self.db.execute("DELETE FROM dbo.RoomCategories WHERE CategoryID = ?", (category_id,))

    # ---------- Номера ----------
    def list_rooms(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM dbo.vw_RoomOccupancy ORDER BY RoomNumber")
            return _rows_to_dicts(cur, cur.fetchall())

    def list_free_rooms(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT r.RoomID, r.RoomNumber, rc.CategoryName, rc.BasePrice, r.Floor "
                "FROM dbo.Rooms AS r "
                "INNER JOIN dbo.RoomCategories AS rc ON rc.CategoryID = r.CategoryID "
                "WHERE r.Status = N'Свободен' "
                "ORDER BY r.RoomNumber"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def add_room(
        self, room_number: str, category_id: int, floor: int, status: str, notes: str | None
    ) -> None:
        self.db.execute(
            "INSERT INTO dbo.Rooms (RoomNumber, CategoryID, Floor, Status, Notes) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_number, category_id, floor, status, notes),
        )

    def update_room(
        self,
        room_id: int,
        room_number: str,
        category_id: int,
        floor: int,
        status: str,
        notes: str | None,
    ) -> None:
        self.db.execute(
            "UPDATE dbo.Rooms "
            "SET RoomNumber = ?, CategoryID = ?, Floor = ?, Status = ?, Notes = ? "
            "WHERE RoomID = ?",
            (room_number, category_id, floor, status, notes, room_id),
        )

    def delete_room(self, room_id: int) -> None:
        self.db.execute("DELETE FROM dbo.Rooms WHERE RoomID = ?", (room_id,))

    # ---------- Гости ----------
    def list_guests(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT GuestID, FullName, PassportNumber, BirthDate, Phone, Email "
                "FROM dbo.Guests ORDER BY FullName"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def add_guest(
        self,
        full_name: str,
        passport: str,
        birth_date: date | None,
        phone: str | None,
        email: str | None,
    ) -> None:
        self.db.execute(
            "INSERT INTO dbo.Guests (FullName, PassportNumber, BirthDate, Phone, Email) "
            "VALUES (?, ?, ?, ?, ?)",
            (full_name, passport, birth_date, phone, email),
        )

    def update_guest(
        self,
        guest_id: int,
        full_name: str,
        passport: str,
        birth_date: date | None,
        phone: str | None,
        email: str | None,
    ) -> None:
        self.db.execute(
            "UPDATE dbo.Guests "
            "SET FullName = ?, PassportNumber = ?, BirthDate = ?, Phone = ?, Email = ? "
            "WHERE GuestID = ?",
            (full_name, passport, birth_date, phone, email, guest_id),
        )

    def delete_guest(self, guest_id: int) -> None:
        self.db.execute("DELETE FROM dbo.Guests WHERE GuestID = ?", (guest_id,))

    # ---------- Сотрудники ----------
    def list_employees(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT EmployeeID, FullName, Position, Phone, HireDate "
                "FROM dbo.Employees ORDER BY FullName"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def add_employee(
        self, full_name: str, position: str, phone: str | None, hire_date: date | None
    ) -> None:
        self.db.execute(
            "INSERT INTO dbo.Employees (FullName, Position, Phone, HireDate) VALUES (?, ?, ?, ?)",
            (full_name, position, phone, hire_date or date.today()),
        )

    def update_employee(
        self,
        employee_id: int,
        full_name: str,
        position: str,
        phone: str | None,
        hire_date: date | None,
    ) -> None:
        self.db.execute(
            "UPDATE dbo.Employees "
            "SET FullName = ?, Position = ?, Phone = ?, HireDate = ? WHERE EmployeeID = ?",
            (full_name, position, phone, hire_date, employee_id),
        )

    def delete_employee(self, employee_id: int) -> None:
        self.db.execute("DELETE FROM dbo.Employees WHERE EmployeeID = ?", (employee_id,))

    # ---------- Услуги ----------
    def list_services(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT ServiceID, ServiceName, Price, Description "
                "FROM dbo.AdditionalServices ORDER BY ServiceName"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def add_service(self, name: str, price: Decimal, description: str | None) -> None:
        self.db.execute(
            "INSERT INTO dbo.AdditionalServices (ServiceName, Price, Description) VALUES (?, ?, ?)",
            (name, price, description),
        )

    def update_service(
        self, service_id: int, name: str, price: Decimal, description: str | None
    ) -> None:
        self.db.execute(
            "UPDATE dbo.AdditionalServices "
            "SET ServiceName = ?, Price = ?, Description = ? WHERE ServiceID = ?",
            (name, price, description, service_id),
        )

    def delete_service(self, service_id: int) -> None:
        self.db.execute("DELETE FROM dbo.AdditionalServices WHERE ServiceID = ?", (service_id,))

    # ---------- Журнал заселений ----------
    def list_active_stays(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT * FROM dbo.vw_ActiveStays ORDER BY CheckInDate DESC"
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def list_all_stays(self, search_text: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM dbo.vw_StayDetails"
        params: tuple[Any, ...] = ()
        if search_text:
            sql += (
                " WHERE GuestFullName LIKE ? "
                "OR PassportNumber LIKE ? "
                "OR RoomNumber LIKE ? "
                "OR EmployeeFullName LIKE ?"
            )
            like = f"%{search_text}%"
            params = (like, like, like, like)
        sql += " ORDER BY CheckInDate DESC"
        with self.db.cursor() as cur:
            cur.execute(sql, *params) if params else cur.execute(sql)
            return _rows_to_dicts(cur, cur.fetchall())

    def get_stay(self, stay_id: int) -> dict[str, Any] | None:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM dbo.vw_StayDetails WHERE StayID = ?", stay_id)
            return _row_to_dict(cur, cur.fetchone())

    @staticmethod
    def _first_select_row(cur: pyodbc.Cursor) -> pyodbc.Row | None:
        """Skip rowcount-only result sets after EXEC and return the first SELECT row."""
        while cur.description is None:
            if not cur.nextset():
                return None
        return cur.fetchone()

    def check_in_guest(
        self,
        room_id: int,
        guest_id: int,
        employee_id: int,
        planned_checkout: date,
        notes: str | None,
    ) -> int:
        with self.db.cursor() as cur:
            cur.execute(
                "DECLARE @id INT; "
                "EXEC dbo.sp_CheckInGuest "
                "@RoomID = ?, @GuestID = ?, @EmployeeID = ?, "
                "@PlannedCheckOutDate = ?, @Notes = ?, @StayID = @id OUTPUT; "
                "SELECT @id AS StayID;",
                room_id, guest_id, employee_id, planned_checkout, notes,
            )
            row = self._first_select_row(cur)
        if row is None or row[0] is None:
            return 0
        return int(row[0])

    def check_out_guest(self, stay_id: int) -> Decimal:
        with self.db.cursor() as cur:
            cur.execute(
                "DECLARE @cost DECIMAL(12,2); "
                "EXEC dbo.sp_CheckOutGuest @StayID = ?, @TotalCost = @cost OUTPUT; "
                "SELECT @cost AS TotalCost;",
                stay_id,
            )
            row = self._first_select_row(cur)
        if row is None or row[0] is None:
            return Decimal("0")
        return Decimal(row[0])

    def add_stay_service(self, stay_id: int, service_id: int, quantity: int = 1) -> None:
        with self.db.cursor() as cur:
            cur.execute(
                "EXEC dbo.sp_AddStayService @StayID = ?, @ServiceID = ?, @Quantity = ?;",
                stay_id, service_id, quantity,
            )

    def list_stay_services(self, stay_id: int) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT ss.StayServiceID, s.ServiceName, ss.ServiceDate, ss.Quantity, ss.Cost "
                "FROM dbo.StayServices AS ss "
                "INNER JOIN dbo.AdditionalServices AS s ON s.ServiceID = ss.ServiceID "
                "WHERE ss.StayID = ? ORDER BY ss.ServiceDate DESC",
                stay_id,
            )
            return _rows_to_dicts(cur, cur.fetchall())

    # ---------- Отчёты ----------
    def get_period_report(
        self,
        start: date,
        end: date,
        category_id: int | None = None,
        employee_id: int | None = None,
    ) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "EXEC dbo.sp_GetReportByPeriod @StartDate = ?, @EndDate = ?, "
                "@CategoryID = ?, @EmployeeID = ?",
                start, end, category_id, employee_id,
            )
            return _rows_to_dicts(cur, cur.fetchall())

    def get_revenue_by_category(self) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute("SELECT * FROM dbo.vw_RevenueByCategory ORDER BY TotalRevenue DESC")
            return _rows_to_dicts(cur, cur.fetchall())

    def get_occupancy_rate(self, start: date, end: date) -> Decimal:
        row = self.db.fetch_one(
            "SELECT dbo.fn_GetOccupancyRate(?, ?) AS Rate", (start, end)
        )
        if row is None or row[0] is None:
            return Decimal("0")
        return Decimal(row[0])

    def get_guest_history(self, guest_id: int) -> list[dict[str, Any]]:
        with self.db.cursor() as cur:
            cur.execute(
                "SELECT * FROM dbo.fn_GetGuestStayHistory(?) ORDER BY CheckInDate DESC", guest_id
            )
            return _rows_to_dicts(cur, cur.fetchall())

    @staticmethod
    def format_dt(value: datetime | date | None) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y %H:%M")
        return value.strftime("%d.%m.%Y")
