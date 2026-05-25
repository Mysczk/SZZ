# I. Relační databázové systémy a OLAP databáze

> Cheat-sheet pro praktickou státnici. Vše na jednom místě s příklady a očekávanými výstupy.

---

## Obsah
1. [Logický návrh & normalizace](#1-logický-návrh--normalizace)
2. [Fyzický návrh – CREATE TABLE](#2-fyzický-návrh--create-table)
3. [Manipulace s daty – INSERT INTO](#3-manipulace-s-daty--insert-into)
4. [Dotazy – SELECT, JOIN, WHERE, ORDER BY, GROUP BY](#4-dotazy)
5. [Transakce](#5-transakce)
6. [Analytické funkce (Window functions)](#6-analytické-funkce-window-functions)
7. [Uložené procedury & Triggery](#7-uložené-procedury--triggery)
8. [Rekurzivní dotazy (CTE)](#8-rekurzivní-dotazy-cte)
9. [Programový přístup – Kurzory & ORM](#9-programový-přístup--kurzory--orm)
10. [Vizualizace – Matplotlib](#10-vizualizace--matplotlib)
11. [OLAP – přehled](#11-olap--přehled)
12. [Architektura DW – Star & Snowflake](#12-architektura-dw--star--snowflake)
13. [Ukázková úloha – workflow](#13-ukázková-úloha--workflow)

---

## 1. Logický návrh & Normalizace

### Relační vztahy
| Vztah | Řešení v DB |
|-------|-------------|
| 1:1   | FK v jedné tabulce + UNIQUE |
| 1:N   | FK na straně „N" |
| M:N   | Vazební tabulka se dvěma FK |

### Normální formy (NF)
| NF | Podmínka |
|----|----------|
| 1NF | Atomické hodnoty, žádné opakující se skupiny |
| 2NF | 1NF + každý neklíčový atribut závisí na **celém** primárním klíči |
| 3NF | 2NF + žádné tranzitivní závislosti (neklíčový → neklíčový) |

### E-R diagram (Crow's foot / vraní nohy)
```
STÁT ||--o{ CIZINEC : "má"
CIZINEC }o--|| POHLAVÍ : "má"
```
- `||` = právě 1 (povinný)
- `o{` = 0 nebo více (volitelný, many)

---

## 2. Fyzický návrh – CREATE TABLE

```sql
-- Číselné domény: INTEGER, BIGINT, NUMERIC(10,2), FLOAT
-- Řetězcové:     VARCHAR(n), CHAR(n), TEXT
-- Časové:        DATE, TIMESTAMP, TIME

CREATE TABLE stat (
    id         SERIAL       PRIMARY KEY,
    kod        CHAR(3)      NOT NULL UNIQUE,   -- ISO 3166-1 alpha-3
    nazev      VARCHAR(100) NOT NULL
);

CREATE TABLE cizinec (
    id         SERIAL       PRIMARY KEY,
    stat_id    INTEGER      NOT NULL REFERENCES stat(id),
    vek        INTEGER      CHECK (vek >= 0 AND vek <= 150),
    pohlaví    CHAR(1)      NOT NULL CHECK (pohlaví IN ('M','F')),
    rok        INTEGER      NOT NULL,
    pocet      INTEGER      NOT NULL DEFAULT 0
);

CREATE TABLE hdp (
    stat_id    INTEGER      NOT NULL REFERENCES stat(id),
    rok        INTEGER      NOT NULL,
    hdp_hlava  NUMERIC(12,2),
    PRIMARY KEY (stat_id, rok)
);
```

**Očekávaný výstup:** Tabulky vytvořeny bez chyb, `\dt` v psql zobrazí nové tabulky.

---

## 3. Manipulace s daty – INSERT INTO

```sql
-- Jednoduchý insert
INSERT INTO stat (kod, nazev) VALUES ('CZE', 'Česko');

-- Hromadný insert
INSERT INTO stat (kod, nazev) VALUES
    ('DEU', 'Německo'),
    ('SVK', 'Slovensko'),
    ('UKR', 'Ukrajina');

-- Insert ze SELECT (přesun/kopie dat)
INSERT INTO hdp (stat_id, rok, hdp_hlava)
SELECT s.id, 2019, 23000.00
FROM stat s WHERE s.kod = 'CZE';

-- Upsert (PostgreSQL) – při konfliktu aktualizuj
INSERT INTO hdp (stat_id, rok, hdp_hlava)
VALUES (1, 2019, 23500.00)
ON CONFLICT (stat_id, rok) DO UPDATE
    SET hdp_hlava = EXCLUDED.hdp_hlava;
```

**Programové načtení dat (Pandas → PostgreSQL):**
```python
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost:5432/statnice")
df = pd.read_csv("cizinci_2019.csv")

# Čištění
df.columns = df.columns.str.lower().str.strip()
df = df.dropna(subset=["stat_kod"])

# Načtení do DB
df.to_sql("cizinec_staging", engine, if_exists="replace", index=False)
```

---

## 4. Dotazy

### SELECT + WHERE + ORDER BY
```sql
SELECT nazev, kod
FROM stat
WHERE nazev LIKE 'U%'        -- začíná na U
ORDER BY nazev ASC;
```
```
nazev       | kod
------------|-----
Uganda      | UGA
Ukrajina    | UKR
Uruguay     | URY
```

### INNER JOIN (jen shody)
```sql
SELECT s.nazev, h.rok, h.hdp_hlava
FROM stat s
INNER JOIN hdp h ON s.id = h.stat_id
WHERE h.rok = 2019
ORDER BY h.hdp_hlava DESC
LIMIT 5;
```

### LEFT JOIN (všichni cizinci, i bez HDP)
```sql
SELECT s.nazev, c.rok, SUM(c.pocet) AS pocet_cizincu, h.hdp_hlava
FROM cizinec c
LEFT JOIN stat s   ON c.stat_id = s.id
LEFT JOIN hdp h    ON c.stat_id = h.stat_id AND c.rok = h.rok
GROUP BY s.nazev, c.rok, h.hdp_hlava
ORDER BY pocet_cizincu DESC;
```

### RIGHT JOIN
```sql
-- Všechny státy v HDP tabulce, i bez cizinců v ČR
SELECT s.nazev, COUNT(c.id) AS pocet
FROM cizinec c
RIGHT JOIN stat s ON c.stat_id = s.id
GROUP BY s.nazev;
```

### GROUP BY + agregace
```sql
SELECT
    s.nazev,
    c.pohlaví,
    SUM(c.pocet)    AS celkem,
    AVG(c.vek)      AS prumer_vek,
    MAX(c.pocet)    AS max_pocet
FROM cizinec c
JOIN stat s ON c.stat_id = s.id
WHERE c.rok = 2019
GROUP BY s.nazev, c.pohlaví
HAVING SUM(c.pocet) > 100        -- filtr AŽ PO seskupení
ORDER BY celkem DESC;
```
```
nazev      | pohlaví | celkem | prumer_vek | max_pocet
-----------|---------|--------|------------|----------
Ukrajina   | M       | 85000  | 34.2       | 12000
Slovensko  | M       | 72000  | 31.8       | 9500
```

---

## 5. Transakce

```sql
BEGIN;

UPDATE hdp SET hdp_hlava = hdp_hlava * 1.05
WHERE rok = 2019;

-- Kontrola
SELECT COUNT(*) FROM hdp WHERE rok = 2019;

-- Pokud OK:
COMMIT;

-- Pokud chyba:
-- ROLLBACK;
```

**Isolation levels (PostgreSQL default = READ COMMITTED):**
```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- ... operace
COMMIT;
```

---

## 6. Analytické funkce (Window functions)

```sql
SELECT
    s.nazev,
    c.rok,
    SUM(c.pocet) AS pocet,
    -- Pořadí v daném roce
    RANK() OVER (PARTITION BY c.rok ORDER BY SUM(c.pocet) DESC) AS poradi,
    -- Kumulativní součet v rámci roku
    SUM(SUM(c.pocet)) OVER (PARTITION BY c.rok
                             ORDER BY SUM(c.pocet) DESC
                             ROWS UNBOUNDED PRECEDING) AS kumulativni,
    -- Podíl z ročního součtu
    ROUND(100.0 * SUM(c.pocet) /
          SUM(SUM(c.pocet)) OVER (PARTITION BY c.rok), 2) AS podil_pct
FROM cizinec c
JOIN stat s ON c.stat_id = s.id
GROUP BY s.nazev, c.rok
ORDER BY c.rok, pocet DESC;
```
```
nazev      | rok  | pocet  | poradi | kumulativni | podil_pct
-----------|------|--------|--------|-------------|----------
Ukrajina   | 2019 | 130000 | 1      | 130000      | 35.20
Slovensko  | 2019 | 115000 | 2      | 245000      | 31.10
```

### Další užitečné funkce
```sql
LAG(pocet, 1)  OVER (PARTITION BY stat_id ORDER BY rok)  -- předchozí rok
LEAD(pocet, 1) OVER (PARTITION BY stat_id ORDER BY rok)  -- příští rok
ROW_NUMBER()   OVER (ORDER BY pocet DESC)                -- unikátní číslo řádku
NTILE(4)       OVER (ORDER BY hdp_hlava)                 -- kvartily
```

---

## 7. Uložené procedury & Triggery

### Procedura
```sql
CREATE OR REPLACE PROCEDURE aktualizuj_hdp(
    p_kod     CHAR(3),
    p_rok     INTEGER,
    p_hdp     NUMERIC
)
LANGUAGE plpgsql AS $$
DECLARE
    v_stat_id INTEGER;
BEGIN
    SELECT id INTO v_stat_id FROM stat WHERE kod = p_kod;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Stát % nenalezen', p_kod;
    END IF;

    INSERT INTO hdp (stat_id, rok, hdp_hlava)
    VALUES (v_stat_id, p_rok, p_hdp)
    ON CONFLICT (stat_id, rok) DO UPDATE SET hdp_hlava = EXCLUDED.hdp_hlava;

    RAISE NOTICE 'HDP pro % (%) aktualizováno na %', p_kod, p_rok, p_hdp;
END;
$$;

-- Volání
CALL aktualizuj_hdp('CZE', 2019, 24500.00);
```

### Trigger
```sql
-- Auditní tabulka
CREATE TABLE audit_log (
    id         SERIAL PRIMARY KEY,
    tabulka    TEXT,
    operace    TEXT,
    cas        TIMESTAMP DEFAULT NOW(),
    uzivatel   TEXT DEFAULT CURRENT_USER
);

-- Trigger funkce
CREATE OR REPLACE FUNCTION log_zmeny()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO audit_log (tabulka, operace)
    VALUES (TG_TABLE_NAME, TG_OP);
    RETURN NEW;  -- pro DELETE použij RETURN OLD
END;
$$;

-- Připojení triggeru
CREATE TRIGGER trg_hdp_audit
AFTER INSERT OR UPDATE OR DELETE ON hdp
FOR EACH ROW EXECUTE FUNCTION log_zmeny();
```

---

## 8. Rekurzivní dotazy (CTE)

```sql
-- Příklad: hierarchie regionů (region → podregion → stát)
WITH RECURSIVE hierarchie AS (
    -- Základní případ (root uzly)
    SELECT id, nazev, parent_id, 0 AS uroven, nazev::TEXT AS cesta
    FROM region
    WHERE parent_id IS NULL

    UNION ALL

    -- Rekurzivní krok
    SELECT r.id, r.nazev, r.parent_id,
           h.uroven + 1,
           h.cesta || ' > ' || r.nazev
    FROM region r
    JOIN hierarchie h ON r.parent_id = h.id
)
SELECT uroven, cesta FROM hierarchie ORDER BY cesta;
```
```
uroven | cesta
-------|-----------------------------
0      | Evropa
1      | Evropa > Střední Evropa
2      | Evropa > Střední Evropa > CZE
```

---

## 9. Programový přístup – Kurzory & ORM

### Kurzor v PL/pgSQL
```sql
CREATE OR REPLACE PROCEDURE zpracuj_cizince()
LANGUAGE plpgsql AS $$
DECLARE
    cur CURSOR FOR SELECT id, pocet FROM cizinec WHERE rok = 2019;
    zaznam cizinec%ROWTYPE;
BEGIN
    OPEN cur;
    LOOP
        FETCH cur INTO zaznam;
        EXIT WHEN NOT FOUND;
        -- zpracování každého řádku
        RAISE NOTICE 'ID: %, pocet: %', zaznam.id, zaznam.pocet;
    END LOOP;
    CLOSE cur;
END;
$$;
```

### ORM – SQLAlchemy (Python)
```python
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, relationship, Session

class Base(DeclarativeBase):
    pass

class Stat(Base):
    __tablename__ = "stat"
    id    = Column(Integer, primary_key=True)
    kod   = Column(String(3), unique=True, nullable=False)
    nazev = Column(String(100), nullable=False)
    hdp_zaznamy = relationship("Hdp", back_populates="stat")

class Hdp(Base):
    __tablename__ = "hdp"
    stat_id   = Column(Integer, ForeignKey("stat.id"), primary_key=True)
    rok       = Column(Integer, primary_key=True)
    hdp_hlava = Column(Numeric(12, 2))
    stat      = relationship("Stat", back_populates="hdp_zaznamy")

engine = create_engine("postgresql://user:pass@localhost/statnice")
Base.metadata.create_all(engine)

with Session(engine) as session:
    czr = Stat(kod="CZE", nazev="Česko")
    session.add(czr)
    session.commit()

    # Dotaz přes ORM
    vysledek = session.query(Stat).filter(Stat.kod == "CZE").first()
    print(vysledek.nazev)  # → Česko
```

---

## 10. Vizualizace – Matplotlib

```python
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/statnice")

# Data ze SQL
df = pd.read_sql("""
    SELECT s.nazev, SUM(c.pocet) AS pocet
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    WHERE c.rok = 2019
    GROUP BY s.nazev
    ORDER BY pocet DESC
    LIMIT 10
""", engine)

# Sloupcový graf
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Graf 1: Top 10 národností
axes[0].barh(df["nazev"], df["pocet"], color="steelblue")
axes[0].set_title("Top 10 národností cizinců v ČR (2019)")
axes[0].set_xlabel("Počet")
axes[0].invert_yaxis()

# Graf 2: Scatter cizinci vs HDP
df2 = pd.read_sql("""
    SELECT s.nazev, SUM(c.pocet) AS pocet, h.hdp_hlava
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    JOIN hdp h  ON c.stat_id = h.stat_id AND c.rok = h.rok
    WHERE c.rok = 2019
    GROUP BY s.nazev, h.hdp_hlava
""", engine)

axes[1].scatter(df2["hdp_hlava"], df2["pocet"], alpha=0.6, color="tomato")
axes[1].set_title("Cizinci vs HDP na hlavu (2019)")
axes[1].set_xlabel("HDP na hlavu (USD)")
axes[1].set_ylabel("Počet cizinců v ČR")

plt.tight_layout()
plt.savefig("vizualizace.png", dpi=150)
plt.show()
```

---

## 11. OLAP – přehled

### OLTP vs OLAP
| Vlastnost | OLTP | OLAP |
|-----------|------|------|
| Účel | Operativní zpracování | Analytické dotazy |
| Operace | INSERT/UPDATE/DELETE | SELECT (čtení) |
| Granularita | Jednotlivé transakce | Agregovaná data |
| Schéma | Normalizované (3NF) | Denormalizované (Star/Snowflake) |
| Dotazy | Jednoduché, rychlé | Komplexní, pomalé |
| Velikost dat | GB | TB–PB |

### Druhy OLAP
| Typ | Uložení | Výhody | Nevýhody |
|-----|---------|--------|----------|
| **ROLAP** | Relační DB | Škálovatelnost, flexibilita | Pomalejší agregace |
| **MOLAP** | Multidim. kostky | Rychlé dotazy | Omezená velikost, preprocessing |
| **HOLAP** | Kombinace | Kompromis | Složitější správa |

### OLAP operace
```
DRILL DOWN  – přechod na detail: rok → kvartál → měsíc
ROLL UP     – agregace: měsíc → rok
SLICE       – řez kostkou: filtr jedné dimenze (rok = 2019)
DICE        – subcube: filtr více dimenzí (rok = 2019 AND stát = CZE)
PIVOT       – rotace (záměna os)
```

---

## 12. Architektura DW – Star & Snowflake

### Star Schema
```sql
-- Tabulka faktů
CREATE TABLE fakt_cizinci (
    id          SERIAL PRIMARY KEY,
    stat_id     INTEGER REFERENCES dim_stat(id),
    cas_id      INTEGER REFERENCES dim_cas(id),
    vek_id      INTEGER REFERENCES dim_vek(id),
    pohlaví_id  INTEGER REFERENCES dim_pohlaví(id),
    pocet       INTEGER NOT NULL
);

-- Dimenzní tabulky (denormalizované = Star)
CREATE TABLE dim_stat (
    id         SERIAL PRIMARY KEY,
    kod        CHAR(3),
    nazev      VARCHAR(100),
    kontinent  VARCHAR(50),    -- denormalizováno sem (ne do extra tabulky)
    hdp_hlava  NUMERIC(12,2)
);

CREATE TABLE dim_cas (
    id      SERIAL PRIMARY KEY,
    datum   DATE,
    rok     INTEGER,
    kvartal INTEGER,
    mesic   INTEGER
);

CREATE TABLE dim_vek (
    id          SERIAL PRIMARY KEY,
    vek         INTEGER,
    vek_skupina VARCHAR(20)  -- '0-14', '15-64', '65+'
);
```

### Snowflake Schema
```sql
-- Normalizovaná verze: kontinent je v extra tabulce
CREATE TABLE dim_kontinent (
    id      SERIAL PRIMARY KEY,
    nazev   VARCHAR(50)
);

CREATE TABLE dim_stat_snow (
    id            SERIAL PRIMARY KEY,
    kod           CHAR(3),
    nazev         VARCHAR(100),
    kontinent_id  INTEGER REFERENCES dim_kontinent(id)  -- FK místo hodnoty
);
```

### DW vs DM
| Pojem | Popis |
|-------|-------|
| **Data Warehouse (DW)** | Celopodnikový sklad, všechna data na jednom místě |
| **Data Mart (DM)** | Výřez DW pro konkrétní oddělení/téma (př. HR, Finance) |

---

## 13. Ukázková úloha – workflow

### Fáze řešení
```
1. Stáhni data (CSV/API)
2. Navrhni ER diagram (entita Stat, Cizinec, HDP)
3. CREATE TABLE v PostgreSQL
4. Python skript: načti CSV → vyčisti (pandas) → INSERT do DB
5. JOIN dotazy + agregace
6. Matplotlib vizualizace
7. Navrhni Star schema pro DW
```

### Klíčové SQL pro ukázkovou úlohu
```sql
-- Seskupení cizinců podle HDP kategorie jejich státu
SELECT
    CASE
        WHEN h.hdp_hlava < 5000   THEN 'Nízký příjem (<5k)'
        WHEN h.hdp_hlava < 20000  THEN 'Střední příjem (5k-20k)'
        ELSE                           'Vysoký příjem (>20k)'
    END AS hdp_kategorie,
    SUM(c.pocet) AS pocet_cizincu,
    COUNT(DISTINCT c.stat_id) AS pocet_statu
FROM cizinec c
JOIN hdp h ON c.stat_id = h.stat_id AND c.rok = h.rok
WHERE c.rok = 2019
GROUP BY hdp_kategorie
ORDER BY pocet_cizincu DESC;
```
```
hdp_kategorie          | pocet_cizincu | pocet_statu
-----------------------|---------------|------------
Vysoký příjem (>20k)   | 215000        | 18
Střední příjem (5k-20k)| 180000        | 34
Nízký příjem (<5k)     | 95000        | 51
```

### Nekonzistence identifikátorů – řešení
```python
# Různé zdroje používají různé kódy zemí → unifikace přes ISO 3166-1 alpha-3
import pycountry

def sjednoť_kod(nazev_statu: str) -> str | None:
    try:
        return pycountry.countries.search_fuzzy(nazev_statu)[0].alpha_3
    except LookupError:
        return None  # ruční doplnění

df["kod_iso"] = df["stat_nazev"].apply(sjednoť_kod)
chybejici = df[df["kod_iso"].isna()]["stat_nazev"].unique()
print("Chybí mapování pro:", chybejici)
```

---

*Aktualizováno pro státnici – PostgreSQL + Python (pandas, SQLAlchemy, matplotlib)*