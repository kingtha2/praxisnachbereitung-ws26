# Tag 4 – Excel-Pipeline mit Power Query

Voraussetzung: Der Stack läuft (`cd inventar-starter && docker compose up -d`),
`http://localhost:8000/assignments.csv` liefert Daten.
Den fertigen M-Code für beide Abfragen gibt es in `docs/powerquery/`.

## Variante 1 – CSV-URL (`inventar_assignment_url.xlsx`)

1. Excel → **Neue leere Arbeitsmappe** → speichern als `inventar_assignment_url.xlsx`.
2. **Daten → Daten abrufen → Aus dem Web**, URL: `http://localhost:8000/assignments.csv`.
3. Im Vorschaufenster auf **Daten transformieren** (nicht direkt „Laden“).
4. Prüfen:
   - **Trennzeichen** = Semikolon (falls alles in einer Spalte steht: Schritt „Quelle“ ⚙ → Trennzeichen `;`,
     Dateiursprung **65001: Unicode (UTF-8)**).
   - **Erste Zeile als Überschriften** verwenden.
   - **Datentypen** je Spalte (Symbol links im Spaltenkopf):
     - `issued_at`, `returned_at` → **Datum** (bei Fehlern: Rechtsklick → Typ ändern → *Mit Gebietsschema…* → Englisch (USA), da ISO-Format `2025-09-30`)
     - `assignment_id`, `duration_days` → **Ganze Zahl**
     - `personnel_no`, `inventory_no`, `serial_no` und alle übrigen → **Text**
5. Abfrage rechts unter *Abfrageeinstellungen* umbenennen in **`AssignmentFromApi`**.
6. **Schließen & laden** → als Tabelle in ein neues Blatt.
7. Test „immer aktuell“: in `/inventory` ein Gerät ausgeben → in Excel **Daten → Alle aktualisieren**
   → neue Zeile erscheint.

Kurzweg: **Daten abrufen → Leere Abfrage → Erweiterter Editor**, Inhalt von
`docs/powerquery/AssignmentFromApi.pq` einfügen, Abfrage `AssignmentFromApi` nennen.

> Hinweis Mac: Bietet euer Excel kein „Aus dem Web“ an, den Kurzweg über die leere Abfrage nehmen.
> Ist auch `Web.Contents` nicht verfügbar, die CSV im Browser herunterladen und über
> „Aus Text/CSV“ einlesen – dann ist es aber keine Live-Verbindung mehr (siehe Vergleich).

## Variante 2 – XLSX-Datei (`inventar_assignment_xlsx.xlsx`)

1. `http://localhost:8000/assignments.xlsx` im Browser herunterladen (landet z. B. in `~/Downloads`).
2. Neue Arbeitsmappe → speichern als `inventar_assignment_xlsx.xlsx`.
3. **Daten → Daten abrufen → Aus Arbeitsmappe** → `assignments.xlsx` auswählen.
4. Im Navigator das Blatt **„Ausleihen“** wählen → **Daten transformieren**.
5. Datentypen prüfen/korrigieren: Power Query übernimmt Datumswerte als *Datum/Uhrzeit* →
   `issued_at`, `returned_at` auf **Datum** stellen; IDs → Ganze Zahl; Nummern → Text.
6. Abfrage umbenennen in **`AssignmentFromXlsx`** → **Schließen & laden**.

Kurzweg: Inhalt von `docs/powerquery/AssignmentFromXlsx.pq` in den Erweiterten Editor einfügen
und den `Pfad` anpassen.

## Pivot-Ideen (auf Basis der geladenen Tabelle)
- Ausleihen je **Gerätetyp** und **Status** (Zeilen: `device_type`, Spalten: `status`, Werte: Anzahl `assignment_id`).
- **Ø Ausleihdauer** je Abteilung (Zeilen: `department`, Werte: Mittelwert `duration_days`).
- Ausleihen je **Monat** (Zeilen: `issued_at` gruppiert nach Jahr/Monat).
- Schäden je Gerätetyp (Filter: `damage_note` ≠ leer).

## 3. Vergleich der Varianten (Stichpunkte für die Präsentation)

**URL-Variante (CSV) ist sinnvoller, wenn …**
- immer der **aktuelle Stand** gebraucht wird: „Aktualisieren“ holt live aus der App, keine Datei-Schieberei.
- regelmäßig dieselbe Auswertung läuft (Dashboard, Wochenreport) → einmal bauen, dann nur aktualisieren.
- mehrere Tools dieselbe Quelle nutzen sollen (Excel, Python, BI) → eine dokumentierte Schnittstelle.
- Nachteil: App muss erreichbar sein (Netz/VPN, später Authentifizierung); Datentypen müssen in
  Power Query gesetzt werden (Text-Format CSV).

**XLSX-Datei ist sinnvoller, wenn …**
- ein **fester Stand** festgehalten werden soll: Monatsabschluss, Inventur zum Stichtag, Audit, Archiv.
- Daten **weitergegeben** werden an Personen ohne Zugriff auf die App (E-Mail, Fileshare).
- offline gearbeitet wird.
- Vorteil: Datentypen und Blattname kommen mit; Nachteil: Datei veraltet sofort, Pfade können
  sich ändern, unklar welche Version die aktuelle ist („Ausleihen_final_v3.xlsx“).

**Empfehlung für einen Fachbereich**
- **Standard: URL-Variante** – eine gepflegte Arbeitsmappe mit Power Query auf `/assignments.csv`,
  Pivots darauf, Aktualisieren per Klick. Daten sind aktuell, Auswertung reproduzierbar,
  keine manuellen Exporte.
- **Ergänzend: XLSX-Snapshots** für Stichtage (z. B. monatlich `assignments_2026-10.xlsx` ablegen),
  wenn ein eingefrorener Stand nachweisbar sein muss.
- Für den produktiven Einsatz fehlt noch: Zugriff ohne `localhost` (Server-URL) und Authentifizierung.
