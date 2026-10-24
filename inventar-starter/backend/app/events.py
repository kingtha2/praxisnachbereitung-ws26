import json
import os
from datetime import date, datetime
from decimal import Decimal

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

TOPIC_ASSIGNMENT_ISSUED = "inventory/assignments/issued"
TOPIC_ASSIGNMENT_RETURNED = "inventory/assignments/returned"


def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"nicht serialisierbar: {type(value).__name__}")


def publish(topic: str, payload: dict) -> None:
    """Publiziert ein Event (QoS 0, kein Retain). Fehler werden nur geloggt,
    damit eine fehlende MQTT-Verbindung die eigentliche Aktion nicht scheitern lässt."""
    try:
        client = mqtt.Client()
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
        client.publish(topic, json.dumps(payload, default=_json_default), qos=0, retain=False)
        client.disconnect()
    except Exception as exc:
        print(f"[MQTT] Publish auf '{topic}' fehlgeschlagen:", exc)


def assignment_payload(row: dict) -> dict:
    return {
        "assignment_id": row["assignment_id"],
        "device_id": row["device_id"],
        "inventory_no": row["inventory_no"],
        "person_id": row["person_id"],
        "personnel_no": row["personnel_no"],
        "issued_at": row["issued_at"],
        "returned_at": row["returned_at"],
    }
