# Tag 4 – Schemaänderung mit Alembic: Schaden-Vermerk

## Warum brauchen wir die Spalte?
- Bei der Rückgabe soll festgehalten werden, ob das Gerät beschädigt zurückkam und was kaputt ist
  (z. B. „Displayriss oben links“).
- Heute ginge das nur über das allgemeine Feld `note`. Das wird aber schon bei der **Ausgabe**
  befüllt („Homeoffice“), Schäden würden darin untergehen und ließen sich nicht auswerten
  (z. B. „Welche Geräte kamen beschädigt zurück?“ → `where damage_note is not null`).
- Der Schaden gehört zur **einzelnen Ausleihe**, nicht zum Gerät: So bleibt nachvollziehbar,
  bei welcher Person / in welchem Zeitraum er entstanden ist.

## Name, Typ, Optionalität
| Entscheidung | Wahl | Überlegung |
|---|---|---|
| Tabelle | `assignment` | Schaden wird bei der Rückgabe (= Ende der Ausleihe) erfasst. |
| Name | `damage_note` | Englisch wie die übrigen Spalten, Suffix `_note` wie das bestehende `note`. |
| Typ | `text` | Freitext unterschiedlicher Länge; in Postgres gibt es keinen Vorteil von `varchar(n)`. |
| Optional? | **ja, `NULL` erlaubt** | Die meisten Rückgaben sind schadensfrei. `NULL` = kein Schaden gemeldet. Außerdem haben die bestehenden Zeilen keinen Wert – mit `NOT NULL` bräuchte es einen Default. |
| Constraint | `damage_note is null or (returned_at is not null and length(trim(damage_note)) > 0)` | Schaden nur bei zurückgegebenen Ausleihen; ein leerer Text zählt nicht als Vermerk. |

Verworfen: zusätzlich `damaged boolean not null default false`. Eine zweite Spalte kann
widersprüchlich werden (`damaged = false`, aber Text vorhanden). „Schaden ja/nein“ ergibt sich
direkt aus `damage_note is not null`.

## Umsetzung
- Alembic im Container (Skript S. 108–112): `alembic` + `SQLAlchemy` in `requirements.txt`,
  `inventar-starter/alembic.ini`, `backend/migrations/env.py` (liest `DB_DSN` aus dem Compose-Service).
- Migration `backend/migrations/versions/20261025_01_assignment_damage_note.py`:
  `upgrade()` → `op.add_column` + Check-Constraint, `downgrade()` → beides wieder entfernen.
- Das Basisschema kommt weiter aus `db/init/*.sql`, daher hat diese erste Migration `down_revision = None`.

## Befehle
```bash
cd inventar-starter
docker compose up -d --build                  # einmalig wegen neuer requirements
docker compose exec api alembic upgrade head  # Migration ausführen
docker compose exec api alembic current       # -> 20261025_01_damage_note (head)
docker compose exec db psql -U appuser -d appdb -c "\d assignment"
docker compose exec api alembic downgrade -1  # Rückweg
```

## Geprüft
- Nach `upgrade head`: Spalte `damage_note text` (nullable) + `assignment_damage_note_check` vorhanden,
  `alembic_version` = `20261025_01_damage_note`.
- Schaden bei zurückgegebener Ausleihe → ok; bei aktiver Ausleihe oder leerem Text → Check-Fehler.
- `downgrade -1` entfernt Spalte und Constraint, `upgrade head` legt sie wieder an. API läuft weiter.

## Achtung
`docker compose down` + `up` initialisiert die DB neu aus `db/init/*.sql` – **ohne** die Spalte.
Danach erneut `alembic upgrade head` ausführen.
