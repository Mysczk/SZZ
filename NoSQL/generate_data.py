"""
Generátor syntetických dat pro ukázku db_olap workflow.
Vytvoří dva CSV soubory:
  data/cizinci.csv  – počty cizinců v ČR podle státu, roku, pohlaví, věkové skupiny
  data/hdp.csv      – HDP na hlavu podle státu a roku
"""

import csv
import random
import os

random.seed(42)

# Vytvoř složku data/ pokud neexistuje
os.makedirs("data", exist_ok=True)

# ── Státy s reálnými kódy ──────────────────────────────────────────────────
STATY = [
    ("UKR", "Ukrajina"),
    ("SVK", "Slovensko"),
    ("VNM", "Vietnam"),
    ("RUS", "Rusko"),
    ("DEU", "Německo"),
    ("POL", "Polsko"),
    ("ROU", "Rumunsko"),
    ("MNG", "Mongolsko"),
    ("CHN", "Čína"),
    ("GBR", "Velká Británie"),
    ("USA", "USA"),
    ("IND", "Indie"),
    ("KAZ", "Kazachstán"),
    ("BLR", "Bělorusko"),
    ("AUT", "Rakousko"),
]

ROKY        = [2017, 2018, 2019, 2020]
POHLAVÍ     = ["M", "F"]
VEK_SKUPINY = ["0-14", "15-34", "35-54", "55+"]

# HDP na hlavu (základ + roční růst) – hrubý odhad v USD
HDP_ZAKLAD = {
    "UKR": 2500,  "SVK": 19000, "VNM": 2700,  "RUS": 11000,
    "DEU": 45000, "POL": 15000, "ROU": 12000,  "MNG": 4000,
    "CHN": 10000, "GBR": 42000, "USA": 62000,  "IND": 2000,
    "KAZ": 9000,  "BLR": 6000,  "AUT": 48000,
}

# ── Generuj cizinci.csv ────────────────────────────────────────────────────
with open("data/cizinci.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["stat_kod", "stat_nazev", "rok", "pohlaví", "vek_skupina", "pocet"])

    for kod, nazev in STATY:
        # Základní počet cizinců pro daný stát (různě velké komunity)
        zaklad = random.randint(500, 50000)
        for rok in ROKY:
            rust = 1 + random.uniform(-0.05, 0.15)   # -5 % až +15 % ročně
            zaklad = int(zaklad * rust)
            for pohl in POHLAVÍ:
                for vek in VEK_SKUPINY:
                    # Ženy vs muži a věkové skupiny mají různé zastoupení
                    koef_pohl = 0.55 if pohl == "M" else 0.45
                    koef_vek  = {"0-14": 0.10, "15-34": 0.40,
                                 "35-54": 0.35, "55+": 0.15}[vek]
                    pocet = max(1, int(zaklad * koef_pohl * koef_vek
                                       * random.uniform(0.85, 1.15)))
                    writer.writerow([kod, nazev, rok, pohl, vek, pocet])

print("✓ data/cizinci.csv vygenerován")

# ── Generuj hdp.csv ────────────────────────────────────────────────────────
with open("data/hdp.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["stat_kod", "rok", "hdp_hlava"])

    for kod, _ in STATY:
        hdp = HDP_ZAKLAD[kod]
        for rok in ROKY:
            hdp = round(hdp * random.uniform(0.97, 1.08), 2)
            writer.writerow([kod, rok, hdp])

print("✓ data/hdp.csv vygenerován")
print("\nPřehled:")
print(f"  Státy:       {len(STATY)}")
print(f"  Roky:        {ROKY}")
print(f"  Řádků cizinci.csv: {len(STATY) * len(ROKY) * len(POHLAVÍ) * len(VEK_SKUPINY)}")
print(f"  Řádků hdp.csv:     {len(STATY) * len(ROKY)}")