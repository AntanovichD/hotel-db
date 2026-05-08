"""Вспомогательные виджеты для форм."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Sequence

import customtkinter as ctk


class DataTable(ctk.CTkFrame):
    """Таблица на основе ttk.Treeview, удобная для CRUD-форм."""

    def __init__(
        self,
        master: tk.Misc,
        columns: Sequence[tuple[str, str, int]],
        on_select: Callable[[dict[str, Any] | None], None] | None = None,
        on_double_click: Callable[[dict[str, Any]], None] | None = None,
        height: int = 14,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.columns_def = list(columns)
        self.on_select = on_select
        self.on_double_click = on_double_click
        self._rows: list[dict[str, Any]] = []

        style = ttk.Style()
        # На Windows 11 родная тема (vista/xpnative) игнорирует фон/цвет
        # заголовков ttk.Treeview, из-за чего шапка выглядит пустой.
        # "clam" уважает все цвета, при этом customtkinter-виджеты не ttk
        # и не зависят от темы.
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(
            "Hotel.Treeview",
            rowheight=26,
            font=("Segoe UI", 11),
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1f1f1f",
            bordercolor="#d0d0d0",
            borderwidth=0,
        )
        style.configure(
            "Hotel.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#1f6aa5",
            foreground="#ffffff",
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "Hotel.Treeview.Heading",
            background=[("active", "#155080"), ("pressed", "#0f3d63")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )
        style.map(
            "Hotel.Treeview",
            background=[("selected", "#3b8ed0")],
            foreground=[("selected", "#ffffff")],
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        col_keys = [c[0] for c in self.columns_def]
        self.tree = ttk.Treeview(
            self,
            columns=col_keys,
            show="headings",
            height=height,
            style="Hotel.Treeview",
        )
        for key, title, width in self.columns_def:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor=tk.W, stretch=True)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.tree.delete(*self.tree.get_children())
        col_keys = [c[0] for c in self.columns_def]
        for idx, row in enumerate(rows):
            values = [row.get(k, "") for k in col_keys]
            self.tree.insert("", tk.END, iid=str(idx), values=values)

    def selected_row(self) -> dict[str, Any] | None:
        selection = self.tree.selection()
        if not selection:
            return None
        try:
            idx = int(selection[0])
        except ValueError:
            return None
        if 0 <= idx < len(self._rows):
            return self._rows[idx]
        return None

    def _on_select(self, _event: object) -> None:
        if self.on_select:
            self.on_select(self.selected_row())

    def _on_double_click(self, _event: object) -> None:
        row = self.selected_row()
        if row is not None and self.on_double_click:
            self.on_double_click(row)


class LabeledEntry(ctk.CTkFrame):
    """Поле ввода с подписью."""

    def __init__(self, master: tk.Misc, label: str, width: int = 240) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(1, weight=1)
        self.label = ctk.CTkLabel(self, text=label, anchor="w")
        self.label.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        self.entry = ctk.CTkEntry(self, width=width)
        self.entry.grid(row=0, column=1, pady=4, sticky="ew")

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: Any) -> None:
        self.entry.delete(0, tk.END)
        if value is not None:
            self.entry.insert(0, str(value))


class LabeledCombo(ctk.CTkFrame):
    """Выпадающий список с подписью."""

    def __init__(
        self,
        master: tk.Misc,
        label: str,
        values: Sequence[str] | None = None,
        width: int = 240,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(1, weight=1)
        self.label = ctk.CTkLabel(self, text=label, anchor="w")
        self.label.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        self.var = ctk.StringVar()
        self.combo = ctk.CTkComboBox(
            self, values=list(values) if values else [], width=width, variable=self.var
        )
        self.combo.grid(row=0, column=1, pady=4, sticky="ew")

    def configure_values(self, values: Sequence[str]) -> None:
        self.combo.configure(values=list(values))

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value or "")
