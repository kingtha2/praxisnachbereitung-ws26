-- 010_inventory_schema.sql
-- Inventar-Schema für Tag 3 (Grundlage: docs/domain.md) mit ein paar Seeddaten.
-- Läuft nur beim ersten Start der DB; nach Änderungen: docker compose down && docker compose up -d --build

-- für das Exclusion-Constraint auf assignment (R1)
create extension if not exists btree_gist;

-- 1. Stammdaten -------------------------------------------------------------

create table if not exists department (
  department_id  serial primary key,
  name           text not null
);
create unique index if not exists department_name_uk on department (lower(name));

create table if not exists location (
  location_id    serial primary key,
  name           text not null
);
create unique index if not exists location_name_uk on location (lower(name));

create table if not exists device_type (
  device_type_id serial primary key,
  name           text not null
);
create unique index if not exists device_type_name_uk on device_type (lower(name));

create table if not exists person (
  person_id      serial primary key,
  personnel_no   text not null unique,
  title          text,
  first_name     text not null,
  last_name      text not null,
  email          text,
  department_id  int  not null references department(department_id),
  location_id    int  not null references location(location_id),
  active         boolean not null default true
);
-- E-Mail optional, aber eindeutig ohne Groß-/Kleinschreibung (mehrere NULL erlaubt)
create unique index if not exists person_email_uk on person (lower(email));

-- 2. Geräte -----------------------------------------------------------------

create table if not exists device (
  device_id          serial primary key,
  inventory_no       text not null unique,
  device_type_id     int  not null references device_type(device_type_id),
  manufacturer       text not null,
  model              text not null,
  serial_no          text unique,                                     -- optional, aber eindeutig
  purchase_date      date not null check (purchase_date <= current_date),            -- R4
  purchase_price_net numeric(10,2) not null check (purchase_price_net >= 0),          -- R6
  location_id        int  not null references location(location_id),
  retired_at         date check (retired_at >= purchase_date)                          -- R7
);

-- 3. Ausleihen --------------------------------------------------------------

create table if not exists assignment (
  assignment_id  serial primary key,
  device_id      int  not null references device(device_id) on delete restrict,  -- R5: nie löschen
  person_id      int  not null references person(person_id) on delete restrict,
  issued_at      date not null default current_date check (issued_at <= current_date),  -- R4
  returned_at    date check (returned_at >= issued_at and returned_at <= current_date), -- R2, R4
  note           text,
  -- R1: Ausleihen desselben Geräts dürfen sich zeitlich nicht überschneiden
  constraint assignment_no_overlap exclude using gist (
    device_id with =,
    daterange(issued_at, returned_at, '[)') with &&
  )
);
-- max. eine aktive Ausleihe pro Gerät
create unique index if not exists assignment_one_active_uk
  on assignment (device_id) where returned_at is null;

-- Nicht per Constraint abgebildet (später in der API prüfen):
--   R3 issued_at >= device.purchase_date, R8 Ausmustern/Deaktivieren nur ohne aktive Ausleihe,
--   R9 Titel nur in title.

-- 4. Seeddaten --------------------------------------------------------------

insert into department (name) values
  ('IT'),
  ('Logistik'),
  ('Verwaltung')
on conflict do nothing;

insert into location (name) values
  ('Gebäude E'),
  ('Gebäude F'),
  ('Gebäude H')
on conflict do nothing;

insert into device_type (name) values
  ('Laptop'),
  ('Monitor'),
  ('Handscanner')
on conflict do nothing;

insert into person (personnel_no, title, first_name, last_name, email, department_id, location_id)
select p.personnel_no, p.title, p.first_name, p.last_name, p.email, d.department_id, l.location_id
from (values
  ('1001', null,    'Anna',  'Koch',    'anna.koch@example.org',    'IT',         'Gebäude E'),
  ('1002', 'Dr.',   'Ben',   'König',   'ben.koenig@example.org',   'Verwaltung', 'Gebäude F'),
  ('1003', null,    'Clara', 'Meier',   'clara.meier@example.org',  'Logistik',   'Gebäude H'),
  ('1004', null,    'David', 'Schulz',  null,                       'Logistik',   'Gebäude H'),
  ('1005', 'Prof.', 'Eva',   'Wagner',  'eva.wagner@example.org',   'IT',         'Gebäude E')
) as p(personnel_no, title, first_name, last_name, email, department, location)
join department d on d.name = p.department
join location l on l.name = p.location
on conflict do nothing;

insert into device (inventory_no, device_type_id, manufacturer, model, serial_no,
                    purchase_date, purchase_price_net, location_id)
select v.inventory_no, t.device_type_id, v.manufacturer, v.model, v.serial_no,
       v.purchase_date::date, v.price::numeric, l.location_id
from (values
  ('G0001', 'Laptop',      'Lenovo', 'ThinkPad T14',  'LNV-T14-0001', '2024-03-01', '1149.00', 'Gebäude E'),
  ('G0002', 'Laptop',      'Dell',   'Latitude 5440', 'DEL-5440-0002', '2024-09-15', '989.00',  'Gebäude F'),
  ('G0003', 'Monitor',     'Dell',   'P2723QE',       'DEL-P27-0003', '2023-11-20', '389.90',  'Gebäude E'),
  ('G0004', 'Monitor',     'LG',     '27UP850',       'LG-27UP-0004', '2025-01-10', '429.00',  'Gebäude F'),
  ('G0005', 'Handscanner', 'Zebra',  'DS2208',        'ZEB-DS22-0005', '2025-04-02', '139.00', 'Gebäude H'),
  ('G0006', 'Handscanner', 'Zebra',  'DS2208',        null,            '2025-04-02', '139.00', 'Gebäude H')
) as v(inventory_no, device_type, manufacturer, model, serial_no, purchase_date, price, location)
join device_type t on t.name = v.device_type
join location l on l.name = v.location
on conflict do nothing;

insert into assignment (device_id, person_id, issued_at, returned_at, note)
select d.device_id, p.person_id, a.issued_at::date, a.returned_at::date, a.note
from (values
  ('G0001', '1001', '2024-03-05', '2025-02-28', 'Rückgabe wegen Neugerät'),
  ('G0001', '1005', '2025-03-03', null,         null),
  ('G0002', '1002', '2024-10-01', null,         'Homeoffice'),
  ('G0003', '1001', '2024-01-08', null,         null),
  ('G0005', '1003', '2025-04-07', '2025-09-30', null),
  ('G0005', '1004', '2025-10-01', null,         'Schichtbetrieb')
) as a(inventory_no, personnel_no, issued_at, returned_at, note)
join device d on d.inventory_no = a.inventory_no
join person p on p.personnel_no = a.personnel_no
on conflict do nothing;
