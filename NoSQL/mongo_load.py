"""
ETL skript: CSV → MongoDB
Používá stejná CSV jako db_olap (data/cizinci.csv, data/hdp.csv)

Struktura dokumentu:
{
  "_id": "UKR",
  "nazev": "Ukrajina",
  "hdp": [ { "rok": 2019, "hdp_hlava": 2755.46 }, ... ],
  "cizinci": [ { "rok": 2019, "pohlaví": "M", "vek_skupina": "15-34", "pocet": 1234 }, ... ]
}
"""

import pandas as pd
from pymongo import MongoClient

# ── Připojení ──────────────────────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017/")
db     = client["szz"]
col    = db["staty"]

# ── 1. Načtení CSV ─────────────────────────────────────────────────────────
print("Načítám CSV...")
df_ciz = pd.read_csv("data/cizinci.csv")
df_hdp = pd.read_csv("data/hdp.csv")

df_ciz.columns = df_ciz.columns.str.lower().str.strip()
df_hdp.columns = df_hdp.columns.str.lower().str.strip()

print(f"  cizinci.csv: {len(df_ciz)} řádků")
print(f"  hdp.csv:     {len(df_hdp)} řádků")

# ── 2. Reset kolekce ───────────────────────────────────────────────────────
col.drop()
print("✓ Kolekce vymazána (fresh start)")

# ── 3. Sestavení a insert dokumentů ───────────────────────────────────────
print("\nSestavuji dokumenty...")
dokumenty = []

for kod, skupina_ciz in df_ciz.groupby("stat_kod"):
    nazev = skupina_ciz["stat_nazev"].iloc[0]

    # HDP záznamy pro tento stát
    hdp_zaznamy = (
        df_hdp[df_hdp["stat_kod"] == kod][["rok", "hdp_hlava"]]
        .to_dict("records")
    )

    # Cizinci záznamy
    cizinci_zaznamy = (
        skupina_ciz[["rok", "pohlaví", "vek_skupina", "pocet"]]
        .to_dict("records")
    )

    doc = {
        "_id":     kod,
        "nazev":   nazev,
        "hdp":     hdp_zaznamy,
        "cizinci": cizinci_zaznamy,
    }
    dokumenty.append(doc)

col.insert_many(dokumenty)
print(f"✓ Vloženo {col.count_documents({})} dokumentů")

# ── 4. Ověření ─────────────────────────────────────────────────────────────
print("\n── Ukázka jednoho dokumentu ───────────────────────")
doc = col.find_one({"_id": "UKR"})
print(f"  _id:    {doc['_id']}")
print(f"  nazev:  {doc['nazev']}")
print(f"  hdp:    {doc['hdp'][:2]}...")
print(f"  cizinci záznamy: {len(doc['cizinci'])}")

print("\n── Počty ───────────────────────────────────────────")
print(f"  Dokumentů v kolekci: {col.count_documents({})}")

# Celkový počet cizinců přes pipeline
pipeline = [
    {"$unwind": "$cizinci"},
    {"$group": {"_id": None, "celkem": {"$sum": "$cizinci.pocet"}}}
]
celkem = list(col.aggregate(pipeline))[0]["celkem"]
print(f"  Celkem cizinců:      {celkem:,}")

print("\n✓ ETL dokončeno")