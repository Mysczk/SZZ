"""
ETL skript: CSV → PostgreSQL
  1. Vytvoří tabulky (stat, cizinec, hdp)
  2. Načte CSV soubory
  3. Vyčistí a transformuje data
  4. Vloží do databáze
"""

import pandas as pd
from sqlalchemy import create_engine, text

# ── Připojení ──────────────────────────────────────────────────────────────
# Uprav heslo pokud jsi zadal jiné při docker run
DB_URL = "postgresql://postgres:admin@localhost:5432/postgres"
engine = create_engine(DB_URL)

# ── 1. Vytvoření tabulek ───────────────────────────────────────────────────
CREATE_TABLES = """
DROP TABLE IF EXISTS cizinec CASCADE;
DROP TABLE IF EXISTS hdp     CASCADE;
DROP TABLE IF EXISTS stat    CASCADE;

CREATE TABLE stat (
    id    SERIAL      PRIMARY KEY,
    kod   CHAR(3)     NOT NULL UNIQUE,
    nazev VARCHAR(100) NOT NULL
);

CREATE TABLE cizinec (
    id          SERIAL  PRIMARY KEY,
    stat_id     INTEGER NOT NULL REFERENCES stat(id),
    rok         INTEGER NOT NULL,
    pohlaví     CHAR(1) NOT NULL CHECK (pohlaví IN ('M','F')),
    vek_skupina VARCHAR(10) NOT NULL,
    pocet       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE hdp (
    stat_id   INTEGER      NOT NULL REFERENCES stat(id),
    rok       INTEGER      NOT NULL,
    hdp_hlava NUMERIC(12,2),
    PRIMARY KEY (stat_id, rok)
);
"""

print("Vytvářím tabulky...")
with engine.begin() as conn:
    conn.execute(text(CREATE_TABLES))
print("✓ Tabulky vytvořeny")

# ── 2. Načtení CSV ─────────────────────────────────────────────────────────
print("\nNačítám CSV...")
df_ciz = pd.read_csv("data/cizinci.csv")
df_hdp = pd.read_csv("data/hdp.csv")

print(f"  cizinci.csv: {len(df_ciz)} řádků")
print(f"  hdp.csv:     {len(df_hdp)} řádků")

# ── 3. Čištění ─────────────────────────────────────────────────────────────
# Sjednoť názvy sloupců
df_ciz.columns = df_ciz.columns.str.strip().str.lower()
df_hdp.columns = df_hdp.columns.str.strip().str.lower()

# Odstraň řádky s chybějícím kódem státu
df_ciz = df_ciz.dropna(subset=["stat_kod"])
df_hdp = df_hdp.dropna(subset=["stat_kod"])

# Ověř typy
df_ciz["pocet"] = pd.to_numeric(df_ciz["pocet"], errors="coerce").fillna(0).astype(int)
df_ciz["rok"]   = df_ciz["rok"].astype(int)
df_hdp["rok"]   = df_hdp["rok"].astype(int)

print("✓ Data vyčištěna")

# ── 4. INSERT do stat ──────────────────────────────────────────────────────
print("\nVkládám státy...")
staty = df_ciz[["stat_kod", "stat_nazev"]].drop_duplicates()

with engine.begin() as conn:
    for _, row in staty.iterrows():
        conn.execute(
            text("INSERT INTO stat (kod, nazev) VALUES (:kod, :nazev) ON CONFLICT (kod) DO NOTHING"),
            {"kod": row["stat_kod"], "nazev": row["stat_nazev"]}
        )

# Načti zpět id → potřebujeme pro FK
with engine.connect() as conn:
    stat_ids = pd.read_sql("SELECT id, kod FROM stat", conn)

print(f"✓ Vloženo {len(stat_ids)} států")

# ── 5. INSERT do hdp ───────────────────────────────────────────────────────
print("Vkládám HDP...")
df_hdp = df_hdp.merge(stat_ids, left_on="stat_kod", right_on="kod")
df_hdp_db = df_hdp[["id", "rok", "hdp_hlava"]].rename(columns={"id": "stat_id"})
df_hdp_db.to_sql("hdp", engine, if_exists="append", index=False)
print(f"✓ Vloženo {len(df_hdp_db)} HDP záznamů")

# ── 6. INSERT do cizinec ───────────────────────────────────────────────────
print("Vkládám cizince...")
df_ciz = df_ciz.merge(stat_ids, left_on="stat_kod", right_on="kod")
df_ciz_db = df_ciz[["id", "rok", "pohlaví", "vek_skupina", "pocet"]].rename(
    columns={"id": "stat_id"}
)
df_ciz_db.to_sql("cizinec", engine, if_exists="append", index=False)
print(f"✓ Vloženo {len(df_ciz_db)} záznamů cizinců")

# ── 7. Ověření ─────────────────────────────────────────────────────────────
print("\n── Ověření ────────────────────────────────")
with engine.connect() as conn:
    for tabulka in ["stat", "cizinec", "hdp"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {tabulka}")).scalar()
        print(f"  {tabulka:10s}: {count} řádků")

print("\n✓ ETL dokončeno – databáze je připravena")