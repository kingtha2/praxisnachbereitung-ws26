from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# Feldnamen entsprechen den Spalten in db/init/010_inventory_schema.sql


class DeviceCreate(BaseModel):
  inventory_no: str = Field(min_length=1, examples=["G0007"])
  device_type_id: int
  manufacturer: str = Field(min_length=1, examples=["Lenovo"])
  model: str = Field(min_length=1, examples=["ThinkPad T14"])
  serial_no: str | None = Field(default=None, examples=["LNV-T14-0007"])
  purchase_date: date
  purchase_price_net: Decimal = Field(ge=0, max_digits=10, decimal_places=2, examples=["999.00"])
  location_id: int


class AssignmentCreate(BaseModel):
  device_id: int
  person_id: int
  issued_at: date | None = None   # leer = heute
  note: str | None = None


class AssignmentReturn(BaseModel):
  returned_at: date | None = None  # leer = heute
