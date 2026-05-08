"""Экспорт отчёта по периоду в формат Microsoft Word (.docx)."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement


COLUMNS: list[tuple[str, str]] = [
    ("RoomNumber", "№ номера"),
    ("CategoryName", "Категория"),
    ("GuestFullName", "Гость"),
    ("PassportNumber", "Паспорт"),
    ("EmployeeFullName", "Сотрудник"),
    ("CheckInDate", "Заселён"),
    ("ActualCheckOutDate", "Выселен"),
    ("Status", "Статус"),
    ("TotalCost", "Стоимость, $"),
]


def _shade_cell(cell, color_hex: str) -> None:
    """Заливка ячейки таблицы цветом."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _format_value(key: str, value: Any) -> str:
    if value is None:
        return ""
    if key == "TotalCost":
        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return str(value)
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y %H:%M") if hasattr(value, "hour") else value.strftime("%d.%m.%Y")
    return str(value)


def export_period_report(
    output_path: Path,
    rows: Iterable[dict[str, Any]],
    start: date,
    end: date,
    category: str | None,
    employee: str | None,
    occupancy: float,
) -> Path:
    """Сформировать отчёт по заселениям за период и сохранить в .docx."""
    rows = list(rows)
    doc = Document()

    # Поля страницы (формат А4)
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    # Заголовок
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("ОТЧЁТ ПО РАБОТЕ ГОСТИНИЦЫ")
    run.bold = True
    run.font.size = Pt(16)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub.add_run(f"Период: {start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}")
    sub_run.font.size = Pt(12)

    # Параметры
    params = doc.add_paragraph()
    params.add_run("Категория: ").bold = True
    params.add_run(category or "Все")
    params.add_run("    Сотрудник: ").bold = True
    params.add_run(employee or "Все")

    # Таблица
    table = doc.add_table(rows=1 + len(rows), cols=len(COLUMNS))
    table.style = "Light Grid Accent 1"
    table.autofit = True

    # Заголовок
    header_row = table.rows[0]
    for idx, (_key, title_text) in enumerate(COLUMNS):
        cell = header_row.cells[idx]
        cell.text = title_text
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        _shade_cell(cell, "1F6AA5")
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in para.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                r.font.size = Pt(10)

    total_cost = 0.0
    for row_idx, row in enumerate(rows, start=1):
        record_row = table.rows[row_idx]
        for col_idx, (key, _t) in enumerate(COLUMNS):
            cell = record_row.cells[col_idx]
            cell.text = _format_value(key, row.get(key))
            for para in cell.paragraphs:
                for r in para.runs:
                    r.font.size = Pt(10)
        try:
            total_cost += float(row.get("TotalCost") or 0)
        except (TypeError, ValueError):
            pass

    # Итоги
    doc.add_paragraph()
    summary = doc.add_paragraph()
    summary.add_run("Всего записей: ").bold = True
    summary.add_run(str(len(rows)))
    summary.add_run("    Общая выручка: ").bold = True
    summary.add_run(f"{total_cost:.2f} $")
    summary.add_run("    Заполняемость номерного фонда: ").bold = True
    summary.add_run(f"{occupancy:.2f} %")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    return output_path
