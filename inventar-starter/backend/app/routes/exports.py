import csv
import io

import pandas as pd
from fastapi import APIRouter, Response

from ..db import get_conn

router = APIRouter(tags=["exports"])

# Reporting-Sicht auf die Ausleihen: eine Zeile pro Ausleihe mit Gerät, Typ, Standorten und Person.
# Spaltenreihenfolge = Reihenfolge in CSV und XLSX.
ASSIGNMENT_EXPORT_SQL = """
    select a.assignment_id,
           case when a.returned_at is null then 'aktiv' else 'zurückgegeben' end as status,
           a.issued_at,
           a.returned_at,
           coalesce(a.returned_at, current_date) - a.issued_at as duration_days,
           d.inventory_no,
           t.name           as device_type,
           d.manufacturer,
           d.model,
           d.serial_no,
           dl.name          as device_location,
           p.personnel_no,
           p.last_name,
           p.first_name,
           dep.name         as department,
           pl.name          as person_location,
           a.note,
           a.damage_note
    from assignment a
    join device d       on d.device_id = a.device_id
    join device_type t  on t.device_type_id = d.device_type_id
    join location dl    on dl.location_id = d.location_id
    join person p       on p.person_id = a.person_id
    join department dep on dep.department_id = p.department_id
    join location pl    on pl.location_id = p.location_id
    order by a.issued_at, a.assignment_id
"""

DATE_COLUMNS = ["issued_at", "returned_at"]


def _fetch_assignment_export() -> tuple[list[str], list[dict]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(ASSIGNMENT_EXPORT_SQL)
        rows = cur.fetchall()
        columns = [c.name for c in cur.description]
    return columns, rows


@router.get("/assignments.csv")
def assignments_csv():
    columns, rows = _fetch_assignment_export()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

    # utf-8-sig: Excel erkennt Umlaute korrekt
    data = buf.getvalue().encode("utf-8-sig")
    headers = {"Content-Disposition": 'attachment; filename="assignments.csv"'}
    return Response(content=data, media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/assignments.xlsx")
def assignments_xlsx():
    columns, rows = _fetch_assignment_export()

    df = pd.DataFrame(rows, columns=columns)
    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col])   # echte Excel-Datumswerte statt Text
    df["duration_days"] = df["duration_days"].astype("int64")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ausleihen")
        sheet = writer.sheets["Ausleihen"]
        sheet.freeze_panes = "A2"               # Kopfzeile fixieren
        sheet.auto_filter.ref = sheet.dimensions
        for idx, col in enumerate(columns, start=1):
            letter = sheet.cell(row=1, column=idx).column_letter
            if col in DATE_COLUMNS:
                for cell in sheet[letter][1:]:
                    cell.number_format = "DD.MM.YYYY"
                width = 10
            else:
                width = max([len(col)] + [len(str(v)) for v in df[col] if pd.notna(v)])
            sheet.column_dimensions[letter].width = min(max(width, len(col)) + 2, 40)

    headers = {"Content-Disposition": 'attachment; filename="assignments.xlsx"'}
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
