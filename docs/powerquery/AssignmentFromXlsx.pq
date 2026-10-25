// Power Query (M) – Variante 2: Ausleihen aus der von der App erzeugten assignments.xlsx
// Abfragename: AssignmentFromXlsx
// Einfügen: Daten > Daten abrufen > Leere Abfrage > Erweiterter Editor
// Vorher: http://localhost:8000/assignments.xlsx herunterladen und den Pfad unten anpassen.
let
    Pfad = "/Users/thai.trinh/Downloads/assignments.xlsx",

    Quelle = Excel.Workbook(File.Contents(Pfad), null, true),
    Blatt = Quelle{[Item = "Ausleihen", Kind = "Sheet"]}[Data],
    Kopfzeile = Table.PromoteHeaders(Blatt, [PromoteAllScalars = true]),

    // Die XLSX bringt echte Datums- und Zahlenwerte mit; Power Query erkennt sie aber
    // zunächst als "any" – darum Typen explizit setzen (Datum ohne Uhrzeit, IDs als Zahl,
    // Nummern als Text)
    Typen = Table.TransformColumnTypes(
        Kopfzeile,
        {
            {"assignment_id", Int64.Type},
            {"status", type text},
            {"issued_at", type date},
            {"returned_at", type date},
            {"duration_days", Int64.Type},
            {"inventory_no", type text},
            {"device_type", type text},
            {"manufacturer", type text},
            {"model", type text},
            {"serial_no", type text},
            {"device_location", type text},
            {"personnel_no", type text},
            {"last_name", type text},
            {"first_name", type text},
            {"department", type text},
            {"person_location", type text},
            {"note", type text},
            {"damage_note", type text}
        }
    )
in
    Typen
