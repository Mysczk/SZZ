# II. NoSQL databáze – MongoDB

> Cheat-sheet pro praktickou státnici. Důraz na dokumentový model, agregační pipeline a vizualizaci.

---

## Obsah
0. [Rychlý start](#0-rychlý-start--spuštění-prostředí)
1. [SQL vs NoSQL – kdy co zvolit](#1-sql-vs-nosql--kdy-co-zvolit)
2. [Dokumentový model – návrh struktury](#2-dokumentový-model--návrh-struktury)
3. [Připojení a vytvoření databáze](#3-připojení-a-vytvoření-databáze)
4. [Programové načtení dat (Insert)](#4-programové-načtení-dat-insert)
5. [Základní dotazy (find)](#5-základní-dotazy-find)
6. [Agregační pipeline](#6-agregační-pipeline)
7. [Denormalizace – embedding vs referencing](#7-denormalizace--embedding-vs-referencing)
8. [BSON/JSON v PostgreSQL (bonus)](#8-bsonjson-v-postgresql-bonus)
9. [Vizualizace – Matplotlib](#9-vizualizace--matplotlib)
10. [Ukázková úloha – workflow](#10-ukázková-úloha--workflow)

---

## 0. Rychlý start – spuštění prostředí

### 1. Spusť MongoDB v Dockeru
```bash
docker run -d \
  --name mongo \
  --restart always \
  -p 27017:27017 \
  mongo
```

### 2. Ověř že běží
```bash
docker ps
# → měl by být vidět kontejner "mongo"
```

### 3. Nainstaluj Python závislosti
```bash
pip install pymongo pandas matplotlib pycountry
```

### 4. Ověř připojení
```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
print(client.list_database_names())
```

### Připojení (MongoDB Compass / mongosh)
```
URI: mongodb://localhost:27017
```

---
## 1. SQL vs NoSQL – kdy co zvolit

### Hodnocení výhod/nevýhod pro otázku u zkoušky

| Kritérium | SQL (PostgreSQL) | NoSQL (MongoDB) |
|-----------|-----------------|-----------------|
| Struktura dat | Pevné schéma, tabulky | Flexibilní, dokumenty (JSON) |
| Vztahy | FK, JOIN | Embedding nebo ruční lookup |
| Transakce | ACID, multi-tabulkové | ACID jen od v4.0, single-doc vždy |
| Škálovatelnost | Vertikální | Horizontální (sharding) |
| Dotazy | SQL – bohatý jazyk | Aggregation pipeline |
| Vhodné pro | ERP, bankovnictví, normalizovaná data | Logy, IoT, dokumenty, heterogenní data |

### Zdůvodnění pro ukázkovou úlohu (cizinci + HDP)
```
✅ MongoDB je vhodné, protože:
  - data z různých zdrojů mají různou strukturu → flexibilní schéma
  - cizinec může mít různé atributy pro různé roky/státy
  - HDP lze embedovat přímo do dokumentu státu
  - žádné složité transakční operace nejsou potřeba

⚠️ SQL by bylo lepší, pokud:
  - potřebujeme silné FK integrity (cizinec MUSÍ odkazovat na existující stát)
  - data jsou striktně normalizovaná a nemění strukturu
  - potřebujeme komplexní multi-tabulkové transakce
```

---

## 2. Dokumentový model – návrh struktury

### Denormalizovaný dokument (doporučeno pro MongoDB)
```json
{
  "_id": "CZE",
  "nazev": "Česko",
  "kontinent": "Evropa",
  "hdp": [
    { "rok": 2018, "hdp_hlava": 22700.0 },
    { "rok": 2019, "hdp_hlava": 23500.0 }
  ],
  "cizinci_v_cr": [
    {
      "rok": 2019,
      "pohlaví": "M",
      "vek_skupina": "25-34",
      "pocet": 1250
    },
    {
      "rok": 2019,
      "pohlaví": "F",
      "vek_skupina": "25-34",
      "pocet": 980
    }
  ]
}
```

> **Klíčový princip:** místo JOIN embedujeme data přímo do dokumentu. Jeden dokument = jeden stát se vším.

---

## 3. Připojení a vytvoření databáze

```python
from pymongo import MongoClient

# Připojení (lokální MongoDB)
client = MongoClient("mongodb://localhost:27017/")

# Databáze a kolekce (vytvoří se automaticky při prvním insertu)
db = client["statnice"]
col_staty = db["staty"]
col_cizinci = db["cizinci"]   # alternativa: flat model

# Ověření připojení
print(client.list_database_names())
# → ['admin', 'local', 'statnice']

print(db.list_collection_names())
# → ['staty', 'cizinci']
```

---

## 4. Programové načtení dat (Insert)

### Načtení a čištění CSV, pak insert do MongoDB
```python
import pandas as pd
from pymongo import MongoClient
import pycountry

client = MongoClient("mongodb://localhost:27017/")
db = client["statnice"]

# --- 1. Načtení CSV ---
df_cizinci = pd.read_csv("cizinci_2019.csv", encoding="utf-8")
df_hdp     = pd.read_csv("hdp.csv", encoding="utf-8")

# --- 2. Čištění ---
df_cizinci.columns = df_cizinci.columns.str.lower().str.strip()
df_hdp.columns     = df_hdp.columns.str.lower().str.strip()

# Sjednocení kódů zemí (různé zdroje = různé názvy)
def sjednoť_kod(nazev: str) -> str | None:
    try:
        return pycountry.countries.search_fuzzy(nazev)[0].alpha_3
    except LookupError:
        return None

df_cizinci["kod_iso"] = df_cizinci["stat"].apply(sjednoť_kod)
df_hdp["kod_iso"]     = df_hdp["country"].apply(sjednoť_kod)

# Zahoď řádky bez kódu
df_cizinci = df_cizinci.dropna(subset=["kod_iso"])
df_hdp     = df_hdp.dropna(subset=["kod_iso"])

# --- 3. Sestavení dokumentů a insert ---
db.staty.drop()  # reset při opakovaném spuštění

for kod, skupina in df_cizinci.groupby("kod_iso"):
    # HDP záznamy pro tento stát
    hdp_zaznam = df_hdp[df_hdp["kod_iso"] == kod][["rok", "hdp_hlava"]].to_dict("records")

    doc = {
        "_id":    kod,
        "nazev":  skupina["stat"].iloc[0],
        "hdp":    hdp_zaznam,
        "cizinci_v_cr": skupina[["rok","pohlaví","vek_skupina","pocet"]].to_dict("records")
    }
    db.staty.insert_one(doc)

print(f"Vloženo {db.staty.count_documents({})} dokumentů")
# → Vloženo 142 dokumentů
```

### Hromadný insert (insert_many)
```python
dokumenty = [
    {"_id": "DEU", "nazev": "Německo", "hdp": [{"rok": 2019, "hdp_hlava": 46000}]},
    {"_id": "SVK", "nazev": "Slovensko", "hdp": [{"rok": 2019, "hdp_hlava": 19200}]},
]
db.staty.insert_many(dokumenty)
```

---

## 5. Základní dotazy (find)

```python
# Najdi jeden dokument
doc = db.staty.find_one({"_id": "CZE"})
print(doc["nazev"])  # → Česko

# Najdi všechny s podmínkou
kursor = db.staty.find(
    {"kontinent": "Evropa"},          # filtr
    {"nazev": 1, "hdp": 1, "_id": 0} # projekce (1=vrať, 0=nevracej)
)
for d in kursor:
    print(d)

# Operátory
db.staty.find({"hdp.hdp_hlava": {"$gt": 30000}})   # hdp_hlava > 30000
db.staty.find({"nazev": {"$in": ["Německo", "Francie"]}})
db.staty.find({"cizinci_v_cr": {"$exists": True}})

# Řazení a limit
db.staty.find().sort("nazev", 1).limit(10)   # 1=ASC, -1=DESC

# Počet
db.staty.count_documents({"kontinent": "Asie"})
```

### Dotaz do vnořeného pole
```python
# Stát, kde máme rok 2019 v HDP
db.staty.find({"hdp": {"$elemMatch": {"rok": 2019, "hdp_hlava": {"$gt": 20000}}}})

# Flat dot-notation (přímý přístup)
db.staty.find({"hdp.rok": 2019})
```

---

## 6. Agregační pipeline

> Pipeline = seznam kroků, každý krok transformuje data. Jako UNIX pipe.

### Základní operátory
| Operátor | SQL ekvivalent | Popis |
|----------|---------------|-------|
| `$match` | WHERE / HAVING | Filtrování dokumentů |
| `$group` | GROUP BY | Seskupení + agregace |
| `$project` | SELECT | Výběr/přejmenování polí |
| `$sort` | ORDER BY | Řazení |
| `$limit` | LIMIT | Omezení počtu |
| `$unwind` | JOIN na pole | Rozbalení pole na řádky |
| `$lookup` | LEFT JOIN | Spojení s jinou kolekcí |
| `$addFields` | computed column | Přidání vypočítaného pole |

---

### Příklad 1: Top 10 státní občanství v ČR (2019)
```python
pipeline = [
    # Rozbal pole cizinci_v_cr na jednotlivé řádky
    {"$unwind": "$cizinci_v_cr"},

    # Filtr rok 2019
    {"$match": {"cizinci_v_cr.rok": 2019}},

    # Seskup podle státu, sečti počet
    {"$group": {
        "_id":   "$_id",
        "nazev": {"$first": "$nazev"},
        "celkem": {"$sum": "$cizinci_v_cr.pocet"}
    }},

    # Seřaď sestupně
    {"$sort": {"celkem": -1}},
    {"$limit": 10}
]

vysledky = list(db.staty.aggregate(pipeline))
for v in vysledky:
    print(f"{v['nazev']:20s} {v['celkem']:>8,}")
```
```
Ukrajina                  130 450
Slovensko                 115 200
Vietnam                    58 100
Rusko                      37 800
...
```

---

### Příklad 2: Cizinci podle HDP kategorie státu (2019)
```python
pipeline = [
    {"$unwind": "$cizinci_v_cr"},
    {"$unwind": "$hdp"},

    # Spoj rok cizince s rokem HDP
    {"$match": {
        "$expr": {"$eq": ["$cizinci_v_cr.rok", "$hdp.rok"]}
    }},

    # Přidej kategorii HDP
    {"$addFields": {
        "hdp_kategorie": {
            "$switch": {
                "branches": [
                    {"case": {"$lt": ["$hdp.hdp_hlava", 5000]},  "then": "Nízký (<5k)"},
                    {"case": {"$lt": ["$hdp.hdp_hlava", 20000]}, "then": "Střední (5k-20k)"},
                ],
                "default": "Vysoký (>20k)"
            }
        }
    }},

    {"$group": {
        "_id":            "$hdp_kategorie",
        "pocet_cizincu":  {"$sum": "$cizinci_v_cr.pocet"},
        "pocet_statu":    {"$addToSet": "$_id"}
    }},

    {"$addFields": {"pocet_statu": {"$size": "$pocet_statu"}}},
    {"$sort": {"pocet_cizincu": -1}}
]

vysledky = list(db.staty.aggregate(pipeline))
```
```
Vysoký (>20k)    | 215 000 cizinců | 18 států
Střední (5k-20k) | 180 000 cizinců | 34 států
Nízký (<5k)      |  95 000 cizinců | 51 států
```

---

### Příklad 3: Seskupení podle pohlaví a věkové skupiny
```python
pipeline = [
    {"$unwind": "$cizinci_v_cr"},
    {"$match": {"cizinci_v_cr.rok": 2019}},
    {"$group": {
        "_id": {
            "pohlaví":    "$cizinci_v_cr.pohlaví",
            "vek_skupina": "$cizinci_v_cr.vek_skupina"
        },
        "celkem": {"$sum": "$cizinci_v_cr.pocet"}
    }},
    {"$sort": {"_id.pohlaví": 1, "_id.vek_skupina": 1}}
]
```

---

### Příklad 4: $lookup (JOIN dvou kolekcí)
```python
# Pokud používáš flat model (2 kolekce místo embedding)
pipeline = [
    {"$lookup": {
        "from":         "hdp",           # druhá kolekce
        "localField":   "_id",           # pole v cizinci
        "foreignField": "stat_kod",      # pole v hdp
        "as":           "hdp_info"       # výsledné pole
    }},
    {"$unwind": {"path": "$hdp_info", "preserveNullAndEmptyArrays": True}},
]
```

---

## 7. Denormalizace – embedding vs referencing

```
EMBEDDING (vše v jednom dokumentu)     REFERENCING (dva dokumenty + lookup)
────────────────────────────────────   ──────────────────────────────────────
✅ Jeden dotaz = všechna data          ✅ Méně duplicit
✅ Rychlé čtení                        ✅ Aktualizace na jednom místě
✅ Atomické operace na dokumentu       ❌ Potřeba $lookup (pomalejší)
❌ Duplicita HDP pro každý stát        ❌ Složitější dotazy
❌ Velké dokumenty (limit 16 MB)

→ Pro státnici volíme EMBEDDING (stát + jeho HDP + jeho cizinci v ČR)
```

---

## 8. BSON/JSON v PostgreSQL (bonus)

```sql
-- PostgreSQL podporuje JSON a JSONB (binární, indexovatelný)
CREATE TABLE staty_json (
    id   SERIAL PRIMARY KEY,
    data JSONB NOT NULL
);

INSERT INTO staty_json (data) VALUES (
    '{"kod":"CZE","nazev":"Česko","hdp_hlava":23500}'
);

-- Dotaz do JSONB
SELECT data->>'nazev' AS nazev,
       (data->>'hdp_hlava')::NUMERIC AS hdp
FROM staty_json
WHERE (data->>'hdp_hlava')::NUMERIC > 20000;

-- Operátory JSONB
-- ->  vrátí JSON objekt/pole
-- ->> vrátí text
-- @>  obsahuje (pro hledání v poli)
SELECT * FROM staty_json
WHERE data @> '{"kontinent":"Evropa"}';
```

---

## 9. Vizualizace – Matplotlib

```python
import matplotlib.pyplot as plt
import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["statnice"]

# --- Data z pipeline ---
pipeline_top10 = [
    {"$unwind": "$cizinci_v_cr"},
    {"$match": {"cizinci_v_cr.rok": 2019}},
    {"$group": {"_id": "$nazev", "celkem": {"$sum": "$cizinci_v_cr.pocet"}}},
    {"$sort": {"celkem": -1}},
    {"$limit": 10}
]
df = pd.DataFrame(db.staty.aggregate(pipeline_top10))
df.columns = ["nazev", "pocet"]

pipeline_hdp = [
    {"$unwind": "$cizinci_v_cr"},
    {"$unwind": "$hdp"},
    {"$match": {"$expr": {"$eq": ["$cizinci_v_cr.rok", "$hdp.rok"]},
                "cizinci_v_cr.rok": 2019}},
    {"$group": {"_id": "$nazev",
                "pocet":     {"$sum": "$cizinci_v_cr.pocet"},
                "hdp_hlava": {"$first": "$hdp.hdp_hlava"}}}
]
df2 = pd.DataFrame(db.staty.aggregate(pipeline_hdp))

# --- Grafy ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Graf 1: Horizontální sloupcový
axes[0].barh(df["nazev"], df["pocet"], color="steelblue")
axes[0].set_title("Top 10 národností cizinců v ČR (2019)")
axes[0].set_xlabel("Počet cizinců")
axes[0].invert_yaxis()
for i, v in enumerate(df["pocet"]):
    axes[0].text(v + 500, i, f"{v:,}", va="center", fontsize=8)

# Graf 2: Scatter cizinci vs HDP
sc = axes[1].scatter(
    df2["hdp_hlava"], df2["pocet"],
    alpha=0.6, c=df2["pocet"], cmap="YlOrRd", s=60
)
axes[1].set_title("Počet cizinců v ČR vs HDP na hlavu státu (2019)")
axes[1].set_xlabel("HDP na hlavu (USD)")
axes[1].set_ylabel("Počet cizinců v ČR")
plt.colorbar(sc, ax=axes[1], label="Počet cizinců")

plt.tight_layout()
plt.savefig("nosql_vizualizace.png", dpi=150)
plt.show()
```

---

## 10. Ukázková úloha – workflow

```
1. Stáhni data (CSV)
2. Navrhni dokumentový model (stát jako root dokument, HDP + cizinci embedded)
3. Python skript:
     - načti CSV (pandas)
     - sjednoť kódy zemí (pycountry)
     - sestav dokumenty
     - insert_many do MongoDB
4. Ověř: find_one, count_documents
5. Agregační pipelines:
     - top 10 státní občanství
     - cizinci podle HDP kategorie
     - rozdělení M/F
6. Matplotlib vizualizace ze dvou pipeline výsledků
7. Zdůvodni: proč MongoDB / proč ne SQL
```

### Instalace závislostí
```bash
pip install pymongo pandas matplotlib pycountry
# MongoDB musí běžet lokálně nebo v Dockeru:
# docker run -d -p 27017:27017 --name mongo mongo:latest
```

### Rychlé ověření dat v shellu (mongosh)
```js
use statnice
db.staty.find().limit(2).pretty()
db.staty.countDocuments()
db.staty.aggregate([{$unwind:"$cizinci_v_cr"},{$count:"celkem_zaznamu"}])
```

---

*Aktualizováno pro státnici – MongoDB + Python (pymongo, pandas, matplotlib)*