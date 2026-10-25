// Power Query (M) – Variante 1: Ausleihen direkt aus der App per CSV-URL
// Abfragename: AssignmentFromApi
// Einfügen: Daten > Daten abrufen > Leere Abfrage > Erweiterter Editor
let
    Url = "http://localhost:8000/assignments.csv",

    // ; als Trennzeichen, UTF-8 (65001) – die App liefert UTF-8 mit BOM
    Quelle = Csv.Document(
        Web.Contents(Url),
        [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Kopfzeile = Table.PromoteHeaders(Quelle, [PromoteAllScalars = true]),

    // leere Felder (z. B. returned_at bei aktiven Ausleihen) als null statt ""
    LeerAlsNull = Table.ReplaceValue(
        Kopfzeile, "", null, Replacer.ReplaceValue,
        {"returned_at", "serial_no", "note", "damage_note"}
    ),

    // Datum kommt als ISO (2025-09-30) -> Kultur "en-US", damit es unabhängig
    // von den Ländereinstellungen des Rechners korrekt gelesen wird
    Typen = Table.TransformColumnTypes(
        LeerAlsNull,
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
            {"personnel_no", type text},   // Text, damit führende Nullen erhalten bleiben
            {"last_name", type text},
            {"first_name", type text},
            {"person_name", type text},
            {"department", type text},
            {"person_location", type text},
            {"note", type text},
            {"damage_note", type text}
        },
        "en-US"
    )
in
    Typen
