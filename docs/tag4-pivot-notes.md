# Tag 4 – Pivot-Auswertungen zur Inventarnutzung

Datenbasis: Abfrage **`AssignmentFromApi`** (Power Query auf `/assignments.csv`, siehe
`tag4-powerquery-notes.md`). Neu im Export: Spalte `person_name` („Nachname, Vorname“).

Pivot anlegen: in die geladene Tabelle klicken → **Einfügen → PivotTable → Neues Arbeitsblatt**.
Je Fragestellung ein eigenes Blatt. Nach neuen Ausleihen in der App: **Daten → Alle aktualisieren**
(aktualisiert Abfrage *und* Pivots).

## Definition „aktiv“
Eine Ausleihe ist **aktiv**, wenn `returned_at` leer ist (Gerät noch nicht zurückgegeben).
Ein Rückgabedatum in der Zukunft gibt es bei uns nicht – das verhindert die DB (`returned_at <= current_date`).
Die App liefert das bereits als Spalte **`status` = „aktiv“**, darauf wird gefiltert.

## 1. Aktive Ausleihen pro Standort
| Bereich | Feld |
|---|---|
| Filter | `status` = aktiv |
| Zeilen | `device_location` (Standort des Geräts) |
| Werte | Anzahl von `assignment_id` |

Erwartetes Ergebnis (Seed-Daten): Gebäude E **2**, Gebäude F **1**, Gebäude H **1** → Gesamt **4**.
Variante: `person_location` statt `device_location` = „Wo arbeiten die Personen mit Geräten?“
(bei den Seed-Daten identisch).

## 2. Nutzung pro DeviceType
| Bereich | Feld |
|---|---|
| Zeilen | `device_type` |
| Werte | Anzahl von `assignment_id` |
| Filter (optional) | `issued_at` → Datumsfilter **„Letzte 12 Monate“** bzw. *Zwischen* 25.10.2025 und heute |

Erwartet (alle Ausleihen): Laptop **3**, Handscanner **2**, Monitor **1**.
Mit 12-Monats-Filter ist das Ergebnis bei den Seed-Daten **leer** – die jüngste Ausgabe war am
01.10.2025. Zum Zeigen in `/inventory` ein, zwei Geräte ausgeben, dann aktualisieren.
Alternative zum Filter: `issued_at` in die Zeilen ziehen und nach **Jahre** gruppieren.

## 3. Geräte pro Person
| Bereich | Feld |
|---|---|
| Filter | `status` = aktiv |
| Zeilen | `person_name` |
| Werte | Anzahl von `assignment_id` |
| Sortierung | absteigend nach Anzahl |

„Wer hat aktuell wie viele Geräte im Einsatz?“ – Seed-Daten: Koch, Anna **1** · König, Ben **1** ·
Schulz, David **1** · Wagner, Eva **1**. (Anna Koch hatte zwei Ausleihen, eine ist zurückgegeben.)
Clara Meier fehlt in der Pivot: Sie hat aktuell kein Gerät (ihre Ausleihe ist zurückgegeben).

## 4. Eigene Fragestellung: Welche Gerätetypen sind am längsten ausgeliehen?
| Bereich | Feld |
|---|---|
| Zeilen | `device_type` |
| Werte | `duration_days` → *Wertfeldeinstellungen* → **Mittelwert**, 0 Nachkommastellen |
| Werte (2.) | Anzahl von `assignment_id` (zur Einordnung) |

Erwartet: Monitor **1021** Tage (1 Ausleihe) · Laptop **≈ 572** (3) · Handscanner **≈ 283** (2).

**Geschäftsfrage:** *Welche Gerätetypen bleiben lange bei den Mitarbeitenden und sollten daher
eher fest zugeordnet als „verliehen“ werden – und für welche lohnt sich ein Ausleih-Pool?*
Monitore werden praktisch dauerhaft genutzt (fester Arbeitsplatz), Handscanner wechseln häufiger
(Schichtbetrieb) → Pool sinnvoll. Hinweis: `duration_days` zählt bei aktiven Ausleihen bis heute.

Weitere Idee mit dem Schaden-Feld aus Aufgabe A: Filter `damage_note` ≠ (leer), Zeilen
`device_location` → „Welche Standorte melden die meisten Schäden?“ (mit den Seed-Daten noch leer,
da `damage_note` bisher nicht über die UI erfasst wird).

## Fazit für die Präsentation
- Eine gut geschnittene Sicht (`/assignments.csv`) reicht für alle Fragen – keine Extra-Exporte nötig.
- Berechnete Spalten in der App (`status`, `duration_days`, `person_name`) machen die Pivots einfach
  und sorgen dafür, dass „aktiv“ überall gleich definiert ist.
- Mit der URL-Variante sind die Pivots nach „Alle aktualisieren“ immer auf dem aktuellen Stand.
