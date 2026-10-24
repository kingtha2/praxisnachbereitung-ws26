# Notizen: Referenzprojekt `grades-starter`

> Tag 3, Aufgabe B. Der `grades-starter` dient nur als **Referenz** für Struktur,
> Formulare, Templates und CRUD-Muster. Entwickelt wird im `inventar-starter`.
> Der Code liegt entpackt außerhalb des Repos unter `~/IdeaProjects/grades-starter`.

## 1. Projektstruktur

```
grades-starter/
├── docker-compose.yml      # db (postgres:16), mqtt (mosquitto:2), api (Build aus Dockerfile)
├── Dockerfile              # python:3.12-slim, uvicorn --reload auf Port 8000
├── requirements.txt        # fastapi, uvicorn, psycopg 3, pydantic 2, Jinja2, paho-mqtt, python-multipart
├── .env                    # nur auskommentierte Overrides (DB_DSN, MQTT_*)
├── db/init/001_schema.sql  # Schema + Seed-Daten, läuft nur beim ersten Start (leeres Volume)
├── mqtt/mosquitto.conf
└── backend/app/
    ├── main.py             # ALLE Routen (HTML-Seiten, Form-POSTs, htmx, CSV, /health)
    ├── db.py               # get_conn()
    ├── models.py           # Pydantic-Models
    ├── mqtt_integration.py # Listener-Thread auf grades/new
    ├── routes/  services/  # leer: vorbereitet, aber nicht genutzt
    └── templates/
        ├── index.html
        ├── students/index.html, students/edit.html
        └── grades/index.html, grades/_list.html   # _list = Partial für htmx
```

- **Kein ORM, keine Migrationen:** Das Schema kommt komplett aus `db/init/*.sql`, das Postgres-Image
  beim ersten Start über `/docker-entrypoint-initdb.d` ausführt. Ändert man das Schema, braucht man
  `docker compose down -v`, sonst bleibt die alte DB im Volume. (`backend/migrations/versions/` ist leer.)
- `backend/` ist als Volume gemountet, und uvicorn läuft mit `--reload`: Code-Änderungen wirken
  sofort, ohne Rebuild. Einen Rebuild braucht man nur bei Änderungen an `requirements.txt` oder am `Dockerfile`.

## 2. Datenbank (`db/init/001_schema.sql`)

| Tabelle   | Spalten                                                         | Constraints                                                                 |
|-----------|-----------------------------------------------------------------|------------------------------------------------------------------------------|
| `student` | `student_id`, `matrikel`, `vorname`, `nachname`, `programme`, `semester` | PK `serial`; `matrikel` **UNIQUE**; alle `NOT NULL`; **CHECK** `semester between 1 and 12` |
| `module`  | `module_id`, `name`                                             | PK `serial`; `name` **UNIQUE NOT NULL**                                      |
| `grade`   | `grade_id`, `student_id`, `module_id`, `grade_value`, `graded_at` | PK; **FK** `student_id → student`, `module_id → module`, beide `ON DELETE CASCADE`; `graded_at default now()` |

- Constraints stehen **inline** in `CREATE TABLE`, es gibt kein separates `ALTER TABLE`.
- `grade` ist die Beziehungstabelle für das n:m zwischen Student und Modul, mit Zusatzattributen.
  Es gibt **kein** UNIQUE auf `(student_id, module_id)`, mehrere Versuche pro Modul sind also erlaubt.
- `grade_value` ist `text` **ohne CHECK**, beliebige Werte wie „1,7“ oder „passed“ gehen durch.
- Seeds sind idempotent: `insert … on conflict do nothing`, die Noten werden per `join` über
  die fachlichen Schlüssel (Matrikel, Modulname) statt über feste IDs eingefügt.

## 3. DB-Zugriff (`backend/app/db.py`)

```python
def get_conn() -> psycopg.Connection:
    return psycopg.connect(DB_DSN, row_factory=dict_row, autocommit=True)
```

Verwendung in jeder Route:

```python
with get_conn() as conn, conn.cursor() as cur:
    cur.execute("select … where student_id = %s", (student_id,))
    row = cur.fetchone()        # dict, z. B. row["matrikel"]
```

- Pro Request wird eine **neue Verbindung** geöffnet, es gibt keinen Pool. Der `with`-Block schließt sie wieder.
- `dict_row`: Zeilen kommen als Dict, damit funktioniert in Jinja `s.matrikel` direkt.
- `autocommit=True`: Jedes Statement ist sofort committet. Für mehrere zusammengehörige Statements
  (z. B. „Ausleihe beenden + neue anlegen“) bräuchte man `with conn.transaction():`.
- Parameter immer als `%s` mit Tupel übergeben, nie per f-String: Das schützt vor SQL-Injection.
- `insert … returning …` liefert die neue Zeile inklusive `id` und Defaults (siehe `create_grade_htmx`).

## 4. API / Routen (alle in `main.py`)

| Methode | Pfad                          | Zweck                                  | Antwort                         |
|---------|-------------------------------|----------------------------------------|---------------------------------|
| GET     | `/`                           | Startseite                             | `index.html`                    |
| GET     | `/students`                   | Liste + Anlege-Formular                | `students/index.html`           |
| POST    | `/students`                   | Student anlegen (Form)                 | Redirect auf `return_to`, sonst Grades-Seite |
| GET     | `/students/{id}/edit`         | Edit-Formular                          | `students/edit.html`            |
| POST    | `/students/{id}/edit`         | Update                                 | 303-Redirect                    |
| POST    | `/students/{id}/delete`       | Löschen (Noten per CASCADE weg)        | 303-Redirect                    |
| POST    | `/modules`                    | Modul anlegen                          | Grades-Seite                    |
| GET     | `/grades?student_id=`         | Notenübersicht + Formulare             | `grades/index.html`             |
| GET     | `/grades/htmx?student_id=`    | nur Notentabelle (htmx)                | `grades/_list.html`             |
| POST    | `/grades/htmx`                | Note anlegen + MQTT `grades/created`   | `grades/_list.html`             |
| GET     | `/grades.csv`                 | CSV-Export (`;`, UTF-8 mit BOM für Excel) | `Response(text/csv)`         |
| GET     | `/health`                     | DB- und MQTT-Check                     | JSON                            |

- Es gibt **keinen** `APIRouter`: Alles hängt direkt an `app`, `routes/` ist leer.
- Es gibt **keine JSON-CRUD-API**, fast alle Routen liefern HTML. In `/docs` tauchen sie trotzdem auf.
- Für Grades und Module gibt es kein Update/Delete, CRUD ist nur bei Students vollständig.

## 5. Models (`backend/app/models.py`)

Pydantic-`BaseModel`, pro Entität nach Zweck getrennt:

- `Student` (mit ID, Lesesicht), `StudentCreate`, `StudentUpdate` (ohne ID, Eingabe)
- `Module` / `ModuleCreate`, `Grade` / `GradeCreate`

Die Models werden nur zur **Validierung der Formulardaten** genutzt
(`data = StudentCreate(matrikel=…, …)`), dann geht `data.feld` ins SQL. Sie dienen **nicht** als
`response_model` und werden nicht von der DB befüllt. Ausnahme: `_ = Grade(**row)` prüft die
Insert-Rückgabe. Die Templates bekommen direkt die `dict_row`-Dicts.

## 6. Formulare: wie werden sie verarbeitet?

1. Ein HTML-`<form method="post" action="/students">` sendet `application/x-www-form-urlencoded`
   (dafür ist `python-multipart` nötig).
2. FastAPI liest jedes Feld einzeln mit `Form(...)`, Typen werden konvertiert (`semester: int = Form(...)`).
   Ein fehlendes oder falsch getyptes Feld liefert **422** als JSON, nicht als hübsche Fehlerseite.
3. Ein Pydantic-Model wird aus den Feldern gebaut, danach folgt das SQL-Statement.
4. Die Antwort folgt dem **Post/Redirect/Get**-Muster: `RedirectResponse(target, status_code=303)`.
   Ein verstecktes Feld `return_to` bestimmt, wohin zurückgesprungen wird
   (dieselbe Route bedient so `/students` und `/grades`).
5. Doppelte Matrikel oder Modulnamen: `on conflict … do nothing` ignoriert sie **stillschweigend**,
   der Nutzer bekommt kein Feedback.

**htmx-Variante (Noten):** `<form hx-post="/grades/htmx" hx-target="#grade-list" hx-swap="innerHTML">`.
Der Server antwortet nur mit dem Partial `_list.html`, htmx tauscht damit den Inhalt von `#grade-list`
aus, ohne die Seite neu zu laden. Das `<select name="student_id">` hat `hx-get` mit
`hx-trigger="change"` und lädt die Tabelle beim Wechsel des Studierenden neu.

## 7. Templates: wie werden sie eingebunden?

```python
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
return templates.TemplateResponse("students/index.html", {"request": request, "title": …, "students": students})
```

- Der Pfad ist relativ zu `templates/`, Unterordner pro Entität (`students/`, `grades/`).
- `request` muss immer im Kontext stehen.
- Jinja-Muster: `{% for s in students %} … {% else %}<em>Keine …</em>{% endfor %}`, Werte vorbelegen mit
  `value="{{ student.matrikel }}"`, Auswahl markieren mit `{% if … %}selected{% endif %}`.
- `{% include "grades/_list.html" %}`: Dasselbe Partial wird beim ersten Laden und bei htmx-Antworten
  gerendert, damit gibt es keine doppelte Tabelle.
- Es gibt **kein** Basis-Layout (`{% extends %}`): Jede Seite ist ein komplettes HTML-Dokument mit eigenem,
  kopiertem `<style>`. htmx kommt per CDN (`unpkg.com/htmx.org@1.9.12`), nur in `grades/index.html`.

## 8. CRUD-Flows (Beispiel Student)

| Schritt   | Request                            | Server                                             | Ergebnis                     |
|-----------|------------------------------------|----------------------------------------------------|------------------------------|
| **List**  | `GET /students`                    | `select … order by nachname` → Template            | Tabelle                      |
| **Create**| `POST /students` (Form)            | `StudentCreate` → `insert … on conflict do nothing` | 303 → `/students`            |
| **Edit**  | `GET /students/5/edit`             | `select … where id=%s`; nicht gefunden → Redirect  | vorbefülltes Formular        |
| **Update**| `POST /students/5/edit` (Form)     | `StudentUpdate` → `update … where id=%s`           | 303 → `/students`            |
| **Delete**| `POST /students/5/delete`          | `delete … where id=%s` (CASCADE auf `grade`)       | 303 → `/students`            |

HTML-Formulare kennen nur GET/POST, deshalb laufen Update und Delete als `POST` auf eigene Unterpfade
(`/edit`, `/delete`) statt als `PUT`/`DELETE`. Das Löschen wird im Browser mit `onsubmit="return confirm(…)"` bestätigt.

## 9. MQTT (Bonus)

- Beim `startup` startet ein Daemon-Thread (`mqtt_integration.py`), der `grades/new` abonniert und bei
  gültigem JSON (`student_id`, `module_id`, `grade_value`) eine Note einfügt. Bei Verbindungsfehlern
  versucht er es alle 5 s erneut.
- Nach dem Anlegen über die UI publiziert die App auf `grades/created`, mit kurzlebigem Client pro Publish.

## 10. Was wir für die Inventar-App übernehmen / anders machen

**Übernehmen:**
- Schema in `db/init/010_inventory_schema.sql` mit Inline-Constraints und idempotenten Seeds.
- `get_conn()` + `with … cursor()` + `%s`-Parameter; `returning` für neue IDs.
- Für jede Entität `XCreate`/`XUpdate`-Models, Formularfelder per `Form(...)`.
- PRG mit 303-Redirect, `return_to`, Edit/Delete als POST-Unterrouten.
- Template-Ordner pro Entität (`devices/`, `assignments/`), Listen-Partial + htmx für Ausleihen.

**Anders / besser machen:**
- `devices.serial_number UNIQUE`, Duplikate aber **sichtbar melden**
  (`UniqueViolation` abfangen, Fehlermeldung im Template) statt `do nothing`.
- „Max. eine aktive Ausleihe“ in der DB absichern, z. B. mit einem partiellen Unique-Index
  `create unique index … on assignment(device_id) where returned_at is null;`
- Mehrschrittige Änderungen in `with conn.transaction():` kapseln.
- Routen mit `APIRouter` in `routes/devices.py` usw. aufteilen statt alles in `main.py`.
- Ein `base.html` mit `{% block content %}` einführen, statt CSS in jede Seite zu kopieren.
- Kein offenes `return_to`: nur interne Pfade zulassen (beginnt mit `/`, nicht mit `//`).
- Bei Schemaänderungen `docker compose down -v` nicht vergessen.
