"""
Dotazy a vizualizace – SQLAlchemy ORM verze.
Spusť až po load_orm.py.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

# Import modelů ze stejného balíčku (nebo zkopíruj definice sem)
from load_orm import Stat, Cizinec, Hdp, engine

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 1 – Top 10 národností v roce 2019
# ══════════════════════════════════════════════════════════════════════════
with Session(engine) as s:
    rows = (
        s.execute(
            select(Stat.nazev, func.sum(Cizinec.pocet).label("pocet"))
            .join(Cizinec, Cizinec.stat_id == Stat.id)
            .where(Cizinec.rok == 2019)
            .group_by(Stat.nazev)
            .order_by(func.sum(Cizinec.pocet).desc())
            .limit(10)
        )
        .all()
    )
df1 = pd.DataFrame(rows, columns=["nazev", "pocet"])
print("── Top 10 národností (2019) ──")
print(df1.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 2 – Vývoj počtu cizinců v letech
# ══════════════════════════════════════════════════════════════════════════
with Session(engine) as s:
    rows = (
        s.execute(
            select(Stat.nazev, Cizinec.rok, func.sum(Cizinec.pocet).label("pocet"))
            .join(Cizinec, Cizinec.stat_id == Stat.id)
            .group_by(Stat.nazev, Cizinec.rok)
            .order_by(Stat.nazev, Cizinec.rok)
        )
        .all()
    )
df2 = pd.DataFrame(rows, columns=["nazev", "rok", "pocet"])

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 3 – Cizinci vs HDP (2019) + window funkce přes raw SQL
# (SQLAlchemy ORM nepodporuje RANK() OVER čistě, proto text() nebo
#  hybrid – zde ukázka s func.rank() + over())
# ══════════════════════════════════════════════════════════════════════════
from sqlalchemy import over

pocet_sum = func.sum(Cizinec.pocet).label("pocet")
rank_pocet = func.rank().over(order_by=func.sum(Cizinec.pocet).desc()).label("rank_pocet")
rank_hdp   = func.rank().over(order_by=Hdp.hdp_hlava.desc()).label("rank_hdp")

with Session(engine) as s:
    rows = (
        s.execute(
            select(
                Stat.nazev,
                pocet_sum,
                Hdp.hdp_hlava,
                rank_pocet,
                rank_hdp,
            )
            .join(Cizinec, Cizinec.stat_id == Stat.id)
            .join(Hdp, (Hdp.stat_id == Stat.id) & (Hdp.rok == Cizinec.rok))
            .where(Cizinec.rok == 2019)
            .group_by(Stat.nazev, Hdp.hdp_hlava)
            .order_by(pocet_sum.desc())
        )
        .all()
    )
df3 = pd.DataFrame(rows, columns=["nazev", "pocet", "hdp_hlava", "rank_pocet", "rank_hdp"])
print("\n── Cizinci vs HDP (2019) ──")
print(df3.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 4 – Rozdělení podle pohlaví (2019)
# ══════════════════════════════════════════════════════════════════════════
with Session(engine) as s:
    rows = (
        s.execute(
            select(Stat.nazev, Cizinec.pohlaví, func.sum(Cizinec.pocet).label("pocet"))
            .join(Cizinec, Cizinec.stat_id == Stat.id)
            .where(Cizinec.rok == 2019)
            .group_by(Stat.nazev, Cizinec.pohlaví)
            .order_by(Stat.nazev)
        )
        .all()
    )
df4 = pd.DataFrame(rows, columns=["nazev", "pohlaví", "pocet"])

# ══════════════════════════════════════════════════════════════════════════
# VIZUALIZACE – identická s původní verzí
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Cizinci v ČR – přehled (ORM)", fontsize=16, fontweight="bold")

ax1 = axes[0, 0]
ax1.barh(df1["nazev"], df1["pocet"], color="steelblue")
ax1.invert_yaxis()
ax1.set_title("Top 10 národností (2019)")
ax1.set_xlabel("Počet cizinců")
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

ax2 = axes[0, 1]
for nazev in df1["nazev"].head(5):
    sub = df2[df2["nazev"] == nazev]
    ax2.plot(sub["rok"], sub["pocet"], marker="o", label=nazev)
ax2.set_title("Vývoj Top 5 (2017–2020)")
ax2.set_xlabel("Rok")
ax2.legend(fontsize=8)
ax2.set_xticks([2017, 2018, 2019, 2020])

ax3 = axes[1, 0]
sc = ax3.scatter(df3["hdp_hlava"], df3["pocet"],
                  c=df3["pocet"], cmap="YlOrRd", s=80, alpha=0.8)
for _, row in df3.iterrows():
    ax3.annotate(row["nazev"], (row["hdp_hlava"], row["pocet"]),
                  textcoords="offset points", xytext=(5, 3), fontsize=7)
ax3.set_title("Počet cizinců vs HDP (2019)")
ax3.set_xlabel("HDP na hlavu (USD)")
plt.colorbar(sc, ax=ax3)

ax4 = axes[1, 1]
df4_pivot = df4.pivot(index="nazev", columns="pohlaví", values="pocet").fillna(0)
df4_pivot.sort_values("M", ascending=False).plot(
    kind="barh", stacked=True, ax=ax4, color=["steelblue", "tomato"]
)
ax4.invert_yaxis()
ax4.set_title("Rozdělení podle pohlaví (2019)")
ax4.legend(["Muži", "Ženy"])

plt.tight_layout()
plt.savefig("vizualizace_orm.png", dpi=150, bbox_inches="tight")
print("\n✓ Graf uložen jako vizualizace_orm.png")
plt.show()