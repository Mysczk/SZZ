"""
ETL skript: CSV → PostgreSQL  (SQLAlchemy ORM verze)
Modely: Stat, Cizinec, Hdp
"""

import pandas as pd
from sqlalchemy import create_engine, String, Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

DB_URL = "postgresql://postgres:admin@localhost:5432/postgres"
engine = create_engine(DB_URL)

# ── ORM modely ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass

class Stat(Base):
    __tablename__ = "stat"

    id:    Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kod:   Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    nazev: Mapped[str] = mapped_column(String(100), nullable=False)

    cizinci:  Mapped[list["Cizinec"]] = relationship(back_populates="stat")
    hdp_data: Mapped[list["Hdp"]]     = relationship(back_populates="stat")

class Cizinec(Base):
    __tablename__ = "cizinec"
    __table_args__ = (
        CheckConstraint("pohlaví IN ('M','F')", name="ck_pohlaví"),
    )

    id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stat_id:     Mapped[int] = mapped_column(ForeignKey("stat.id"), nullable=False)
    rok:         Mapped[int] = mapped_column(Integer, nullable=False)
    pohlaví:     Mapped[str] = mapped_column(String(1), nullable=False)
    vek_skupina: Mapped[str] = mapped_column(String(10), nullable=False)
    pocet:       Mapped[int] = mapped_column(Integer, default=0)

    stat: Mapped["Stat"] = relationship(back_populates="cizinci")

class Hdp(Base):
    __tablename__ = "hdp"

    stat_id:   Mapped[int]   = mapped_column(ForeignKey("stat.id"), primary_key=True)
    rok:       Mapped[int]   = mapped_column(Integer, primary_key=True)
    hdp_hlava: Mapped[float] = mapped_column(Numeric(12, 2))

    stat: Mapped["Stat"] = relationship(back_populates="hdp_data")

# ── Vytvoření tabulek ──────────────────────────────────────────────────────
print("Vytvářím tabulky...")
Base.metadata.drop_all(engine)   # DROP + CREATE (čistý start)
Base.metadata.create_all(engine)
print("✓ Tabulky vytvořeny")

# ── Načtení CSV ────────────────────────────────────────────────────────────
print("\nNačítám CSV...")
df_ciz = pd.read_csv("data/cizinci.csv")
df_hdp = pd.read_csv("data/hdp.csv")
df_ciz.columns = df_ciz.columns.str.strip().str.lower()
df_hdp.columns = df_hdp.columns.str.strip().str.lower()
df_ciz = df_ciz.dropna(subset=["stat_kod"])
df_hdp = df_hdp.dropna(subset=["stat_kod"])
df_ciz["pocet"] = pd.to_numeric(df_ciz["pocet"], errors="coerce").fillna(0).astype(int)
df_ciz["rok"]   = df_ciz["rok"].astype(int)
df_hdp["rok"]   = df_hdp["rok"].astype(int)
print("✓ Data vyčištěna")

# ── INSERT přes ORM ────────────────────────────────────────────────────────
print("\nVkládám data přes ORM...")

with Session(engine) as session:

    # 1. Státy
    staty_df = df_ciz[["stat_kod", "stat_nazev"]].drop_duplicates()
    stat_map: dict[str, Stat] = {}  # kod → objekt

    for _, row in staty_df.iterrows():
        stat = Stat(kod=row["stat_kod"], nazev=row["stat_nazev"])
        session.add(stat)
        stat_map[row["stat_kod"]] = stat

    session.flush()  # přidělí id, ale transakce ještě neuzavřena
    print(f"  ✓ {len(stat_map)} států")

    # 2. HDP
    hdp_objekty = [
        Hdp(
            stat_id=stat_map[row["stat_kod"]].id,
            rok=row["rok"],
            hdp_hlava=row["hdp_hlava"],
        )
        for _, row in df_hdp.iterrows()
        if row["stat_kod"] in stat_map
    ]
    session.add_all(hdp_objekty)
    print(f"  ✓ {len(hdp_objekty)} HDP záznamů")

    # 3. Cizinci
    cizinec_objekty = [
        Cizinec(
            stat_id=stat_map[row["stat_kod"]].id,
            rok=row["rok"],
            pohlaví=row["pohlaví"],
            vek_skupina=row["vek_skupina"],
            pocet=row["pocet"],
        )
        for _, row in df_ciz.iterrows()
        if row["stat_kod"] in stat_map
    ]
    session.add_all(cizinec_objekty)
    print(f"  ✓ {len(cizinec_objekty)} záznamů cizinců")

    session.commit()
    print("\n✓ Commit – vše uloženo")

# ── Ověření přes ORM ───────────────────────────────────────────────────────
print("\n── Ověření ────────────────────────────────")
with Session(engine) as session:
    from sqlalchemy import func, select

    for model, label in [(Stat, "stat"), (Cizinec, "cizinec"), (Hdp, "hdp")]:
        count = session.scalar(select(func.count()).select_from(model))
        print(f"  {label:10s}: {count} řádků")

print("\n✓ ETL (ORM) dokončeno")