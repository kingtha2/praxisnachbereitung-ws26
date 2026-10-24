from datetime import date

from fastapi import APIRouter, HTTPException, status
from psycopg import errors

from ..db import get_conn
from ..models import AssignmentCreate, AssignmentReturn

router = APIRouter(prefix="/assignments", tags=["assignments"])

ASSIGNMENT_SELECT = """
    select a.assignment_id, a.issued_at, a.returned_at, a.note,
           a.device_id, d.inventory_no, d.serial_no, t.name as device_type,
           d.manufacturer, d.model,
           a.person_id, p.personnel_no, p.first_name, p.last_name
    from assignment a
    join device d on d.device_id = a.device_id
    join device_type t on t.device_type_id = d.device_type_id
    join person p on p.person_id = a.person_id
"""


def _get_assignment(cur, assignment_id: int):
    cur.execute(ASSIGNMENT_SELECT + " where a.assignment_id = %s", (assignment_id,))
    return cur.fetchone()


@router.get("/active")
def list_active_assignments():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(ASSIGNMENT_SELECT + " where a.returned_at is null order by a.issued_at desc")
        return cur.fetchall()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assignment(data: AssignmentCreate):
    issued_at = data.issued_at or date.today()
    if issued_at > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "issued_at darf nicht in der Zukunft liegen")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select purchase_date, retired_at from device where device_id = %s", (data.device_id,))
        device = cur.fetchone()
        if not device:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Gerät {data.device_id} nicht gefunden")
        if device["retired_at"] is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Gerät ist ausgemustert")
        if issued_at < device["purchase_date"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "issued_at darf nicht vor dem Kaufdatum liegen")

        cur.execute("select active from person where person_id = %s", (data.person_id,))
        person = cur.fetchone()
        if not person:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Person {data.person_id} nicht gefunden")
        if not person["active"]:
            raise HTTPException(status.HTTP_409_CONFLICT, "Person ist deaktiviert")

        # IR-02: max. eine aktive Ausleihe pro Gerät
        cur.execute(
            "select assignment_id from assignment where device_id = %s and returned_at is null",
            (data.device_id,),
        )
        active = cur.fetchone()
        if active:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Gerät ist bereits ausgeliehen (Ausleihe {active['assignment_id']})",
            )

        try:
            cur.execute(
                """
                insert into assignment (device_id, person_id, issued_at, note)
                values (%s, %s, %s, %s)
                returning assignment_id
                """,
                (data.device_id, data.person_id, issued_at, data.note),
            )
        except (errors.UniqueViolation, errors.ExclusionViolation):
            # gleichzeitige Ausleihe oder Überschneidung mit einer früheren Ausleihe (R1)
            raise HTTPException(status.HTTP_409_CONFLICT, "Ausleihe überschneidet sich mit einer bestehenden Ausleihe")
        return _get_assignment(cur, cur.fetchone()["assignment_id"])


@router.post("/{assignment_id}/return")
def return_assignment(assignment_id: int, data: AssignmentReturn | None = None):
    returned_at = (data.returned_at if data else None) or date.today()

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select issued_at, returned_at from assignment where assignment_id = %s", (assignment_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Ausleihe {assignment_id} nicht gefunden")
        if row["returned_at"] is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Ausleihe wurde bereits am {row['returned_at']} zurückgegeben")
        # IR-03: returned_at nicht vor issued_at
        if returned_at < row["issued_at"]:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"returned_at ({returned_at}) darf nicht vor issued_at ({row['issued_at']}) liegen",
            )
        if returned_at > date.today():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "returned_at darf nicht in der Zukunft liegen")

        cur.execute(
            "update assignment set returned_at = %s where assignment_id = %s and returned_at is null",
            (returned_at, assignment_id),
        )
        return _get_assignment(cur, assignment_id)
