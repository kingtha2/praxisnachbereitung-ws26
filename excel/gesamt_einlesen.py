from pathlib import Path

import pandas as pd

EXCEL = Path(__file__).parent / "Geraeteverwaltung.xlsx"

gesamt = pd.read_excel(EXCEL, sheet_name="Gesamt")

print(f"{len(gesamt)} Ausleihen, {len(gesamt.columns)} Spalten")
print(gesamt.head())
print()
print("Ausleihen pro Gerätetyp:")
print(gesamt["Gerätetyp"].value_counts())
