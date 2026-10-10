# praxisnachbereitung-ws26

Aufgabe B:

Fehler:
- G0011, G0022, G0031: Kaufdatum liegt nach Ausgabe des Produkts.
- Zeitliche Überschneidung mit Ausleihe, z.B. G0035 (Zeile 20,31), G0024 (Zeile 4, 12)

Aufgabe D: 

=COUNTIFS(Ausleihen!$A$2:$A$46;A1;Ausleihen!$D$2:$D$46;"")
Zählt für das Gerät die Ausleihen ohne Rückgabedatum (= offene Ausleihen).
Bedingung 1: Gerätenummer im Blatt Ausleihen (Spalte A) ist gleich A1.
Bedingung 2: „Rückgabe am“ im Blatt Ausleihen (Spalte D) ist leer.
Ergebnis 0 → Gerät ist nicht im Einsatz.
Ergebnis ≥ 1 → Gerät ist im Einsatz.


Gefiltert aus Gesamt nach Gerätetyp = "Laptop" 
Im Bestand sind 9 Laptops, davon wurden 7 mindestens einmal ausgeliehen; nie ausgeliehen: G0010, G0026.


# Geräteverwaltung – Datenanalyse in Excel

Analyse von Geräten, Mitarbeitern und Ausleihen auf Basis von drei CSV-Dateien.

## Dateien

- `excel/Geraeteverwaltung.xlsx` – Arbeitsmappe mit Quelldaten, Gesamttabelle und Auswertungen
- `excel/Gesamt_bereinigt.csv` – bereinigte Gesamttabelle (UTF-8, Trennzeichen `;`, Datum TT.MM.JJJJ)
- `gesamt_einlesen.py` – liest die Gesamttabelle per Python aus der Excel-Datei und schreibt die CSV
