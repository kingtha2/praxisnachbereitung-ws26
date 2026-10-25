# Tag 4 – Assignment-Exports per HTTP

## 1. Spalten der Assignment-Sicht
Eine Zeile pro Ausleihe. Reihenfolge: erst die Ausleihe, dann das Gerät, dann die Person.

| # | Spalte | Herkunft | Wozu im Reporting |
|---|---|---|---|
| 1 | `assignment_id` | assignment | eindeutige Zeile, Rückverfolgung in die App |
| 2 | `status` | berechnet: `aktiv` / `zurückgegeben` | Filter/Pivot „Was ist gerade draußen?“ |
| 3 | `issued_at` | assignment | Zeitachse (Monat/Jahr) |
| 4 | `returned_at` | assignment | leer = noch ausgeliehen |
| 5 | `duration_days` | berechnet: `coalesce(returned_at, heute) - issued_at` | Ø Ausleihdauer je Typ/Abteilung |
| 6 | `inventory_no` | device | fachlicher Schlüssel des Geräts |
| 7 | `device_type` | device_type | Pivot je Gerätetyp |
| 8 | `manufacturer` | device | Auswertung je Hersteller |
| 9 | `model` | device | |
| 10 | `serial_no` | device | Abgleich mit Hersteller/Garantie |
| 11 | `device_location` | location (über device) | Wo steht das Gerät? |
| 12 | `personnel_no` | person | fachlicher Schlüssel der Person |
| 13 | `last_name` | person | |
| 14 | `first_name` | person | |
| 15 | `person_name` | berechnet: „Nachname, Vorname“ | Pivot je Person (Aufgabe D) |
| 16 | `department` | department (über person) | Pivot je Abteilung |
| 17 | `person_location` | location (über person) | Wo arbeitet die Person? |
| 18 | `note` | assignment | Freitext zur Ausgabe |
| 19 | `damage_note` | assignment (Migration aus Aufgabe A) | Schadensquote je Typ/Abteilung |

Bewusst nicht enthalten: technische IDs (`device_id`, `person_id`, …), Kaufpreis (gehört in eine
Geräte- statt in eine Ausleihsicht), E-Mail (Datensparsamkeit).

## 2. SQL-Join
Startet bei `assignment` und verbindet `device`, `device_type`, `location` (zweimal: Gerät und
Person), `person` und `department`. Alle Joins sind `inner join`, weil die FKs `NOT NULL` sind.
Sortiert nach `issued_at`. → `ASSIGNMENT_EXPORT_SQL` in
`inventar-starter/backend/app/routes/exports.py`.

## 3./4. Endpunkte
| Endpunkt | Format | Details |
|---|---|---|
| `GET /assignments.csv` | CSV | `;` als Trennzeichen, Header-Zeile, UTF-8 mit BOM (`utf-8-sig`), Datum ISO `2025-09-30` |
| `GET /assignments.xlsx` | Excel | pandas + `ExcelWriter`/openpyxl, Sheet „Ausleihen“, Datum als echte Excel-Daten (`DD.MM.YYYY`), fixierte Kopfzeile, Autofilter, Spaltenbreiten |

Beide nutzen dieselbe Abfrage, damit CSV und XLSX immer identische Daten haben.
Links dazu stehen oben auf `/inventory`.

## 5. Test
- Beide Endpunkte liefern HTTP 200 mit `Content-Disposition: attachment`.
- CSV: 6 Datenzeilen + Header, BOM vorhanden, Umlaute korrekt.
- XLSX geprüft: `issued_at`/`returned_at` = Datum, `duration_days`/`assignment_id` = Zahl,
  `personnel_no`/`inventory_no` = Text (keine abgeschnittenen führenden Nullen), leere Felder bleiben leer.
- Gespeicherte Dateien: `docs/exports/assignments.csv`, `docs/exports/assignments.xlsx`
  (Seed-Daten, eine Rückgabe mit Test-Schaden).

## CSV vs. XLSX – Unterschied in der Nutzung für unsere App
**CSV (`/assignments.csv`)**
- Offene, maschinenlesbare Schnittstelle: Power Query („Aus dem Web“), Python/pandas, BI-Tools, Skripte.
- Als **URL** direkt als Datenquelle nutzbar → Aktualisieren holt immer den aktuellen Stand, kein Datei-Hin-und-Her.
- Nur Text: Datentypen (Datum, Zahl) muss der Empfänger selbst setzen; Trennzeichen/Encoding
  können Probleme machen (deshalb `;` und BOM).
- Klein, einfach, versionierbar → gut für Automatisierung und Pipelines.

**XLSX (`/assignments.xlsx`)**
- Für Fachanwender:innen „zum Anklicken“: Datei öffnen und sofort lesbar.
- Datentypen kommen mit (Datum ist Datum, Zahl ist Zahl), dazu Formatierung, Filter, fixierte
  Kopfzeile; mehrere Sheets wären möglich.
- Eher ein **Schnappschuss**: Wer die Datei speichert, hat einen Stand von gestern;
  für Pipelines schwerer zu verarbeiten als CSV und abhängig von pandas/openpyxl im Backend.

**Fazit:** CSV-URL als stabile Datenquelle für Power Query/Pivot-Auswertungen (Aufgabe C),
XLSX für den schnellen Export „mal eben in Excel anschauen oder weitergeben“.
