from datetime import date

from fastapi import APIRouter, HTTPException, status
from psycopg import errors

from ..db import get_conn
from ..models import DeviceCreate

router = APIRouter(prefix="/devices", tags=["devices"])

DEVICE_SELECT = """
    select d.device_id, d.inventory_no, d.manufacturer, d.model, d.serial_no,
           d.purchase_date, d.purchase_price_net, d.retired_at,
           d.device_type_id, t.name as device_type,
           d.location_id, l.name as location,
           a.assignment_id as active_assignment_id
    from device d
    join device_type t on t.device_type_id = d.device_type_id
    join location l on l.location_id = d.location_id
    left join assignment a on a.device_id = d.device_id and a.returned_at is null
"""


@router.get("")
def list_devices():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(DEVICE_SELECT + " order by d.inventory_no")
        return cur.fetchall()


@router.get("/{device_id}")
def get_device(device_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(DEVICE_SELECT + " where d.device_id = %s", (device_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Gerät {device_id} nicht gefunden")
    return row


@router.post("", status_code=status.HTTP_201_CREATED)
def create_device(data: DeviceCreate):
    if data.purchase_date > date.today():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "purchase_date darf nicht in der Zukunft liegen")

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into device (inventory_no, device_type_id, manufacturer, model, serial_no,
                                    purchase_date, purchase_price_net, location_id)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                returning device_id
                """,
                (data.inventory_no, data.device_type_id, data.manufacturer, data.model,
                 data.serial_no or None, data.purchase_date, data.purchase_price_net, data.location_id),
            )
            device_id = cur.fetchone()["device_id"]
    except errors.UniqueViolation as exc:
        # IR-01: Seriennummer (und Inventarnummer) eindeutig
        if exc.diag.constraint_name == "device_serial_no_key":
            raise HTTPException(status.HTTP_409_CONFLICT, f"Seriennummer '{data.serial_no}' existiert bereits")
        raise HTTPException(status.HTTP_409_CONFLICT, f"Inventarnummer '{data.inventory_no}' existiert bereits")
    except errors.ForeignKeyViolation:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "device_type_id oder location_id existiert nicht")

    return get_device(device_id)
