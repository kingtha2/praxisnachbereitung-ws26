from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from datetime import date
from .db import get_conn
from .routes import assignments, devices, exports
import paho.mqtt.client as mqtt

app = FastAPI(title="Inventar Starter", version="0.1.0")
app.include_router(devices.router)
app.include_router(assignments.router)
app.include_router(exports.router)
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

def mqtt_client() -> mqtt.Client:
    c = mqtt.Client()
    c.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    return c

@app.get("/health")
async def health():
    db_state = "ok"
    mqtt_state = "ok"
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("select 1")
            cur.fetchone()
    except Exception as ex:
        db_state = f"error:{type(ex).__name__}"

    try:
        c = mqtt_client()
        c.disconnect()
    except Exception as ex:
        mqtt_state = f"degraded:{type(ex).__name__}"

    return {"status": "ok" if db_state == "ok" else "degraded", "db": db_state, "mqtt": mqtt_state}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Inventar Starter"})

@app.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request):
    device_list = devices.list_devices()
    active_assignments = assignments.list_active_assignments()

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("select device_type_id, name from device_type order by name")
        device_types = cur.fetchall()
        cur.execute("select location_id, name from location order by name")
        locations = cur.fetchall()
        cur.execute(
            "select person_id, personnel_no, first_name, last_name from person where active order by last_name, first_name"
        )
        persons = cur.fetchall()

    for d in device_list:
        if d["retired_at"]:
            d["status"] = "ausgemustert"
        elif d["active_assignment_id"]:
            d["status"] = "ausgeliehen"
        else:
            d["status"] = "frei"
    free_devices = [d for d in device_list if d["status"] == "frei"]

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "title": "Inventar",
            "devices": device_list,
            "free_devices": free_devices,
            "active_assignments": active_assignments,
            "device_types": device_types,
            "locations": locations,
            "persons": persons,
            "today": date.today().isoformat(),
        },
    )

@app.post("/mqtt/publish")
async def mqtt_publish(topic: str = Query(...), payload: str = Query(...)):
    c = mqtt_client()
    c.publish(topic, payload, qos=0, retain=False)
    c.disconnect()
    return {"ok": True, "topic": topic, "payload": payload}
