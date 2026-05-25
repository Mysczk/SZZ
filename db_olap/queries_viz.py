"""
Dotazy a vizualizace nad načtenými daty.
Spusť až po load_data.py.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:admin@localhost:5432/postgres"
engine = create_engine(DB_URL)

# ── Helper ─────────────────────────────────────────────────────────────────
def sql(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(query, conn)

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 1 – Top 10 národností v roce 2019
# ══════════════════════════════════════════════════════════════════════════
df1 = sql("""
    SELECT s.nazev, SUM(c.pocet) AS pocet
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    WHERE c.rok = 2019
    GROUP BY s.nazev
    ORDER BY pocet DESC
    LIMIT 10
""")
print("── Top 10 národností (2019) ──")
print(df1.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 2 – Vývoj počtu cizinců v letech (všechny roky)
# ══════════════════════════════════════════════════════════════════════════
df2 = sql("""
    SELECT s.nazev, c.rok, SUM(c.pocet) AS pocet
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    GROUP BY s.nazev, c.rok
    ORDER BY s.nazev, c.rok
""")

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 3 – Cizinci vs HDP na hlavu (2019) + window funkce
# ══════════════════════════════════════════════════════════════════════════
df3 = sql("""
    SELECT
        s.nazev,
        SUM(c.pocet)  AS pocet,
        h.hdp_hlava,
        RANK() OVER (ORDER BY SUM(c.pocet) DESC) AS rank_pocet,
        RANK() OVER (ORDER BY h.hdp_hlava   DESC) AS rank_hdp
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    JOIN hdp  h ON c.stat_id = h.stat_id AND c.rok = h.rok
    WHERE c.rok = 2019
    GROUP BY s.nazev, h.hdp_hlava
    ORDER BY pocet DESC
""")
print("\n── Cizinci vs HDP (2019) ──")
print(df3.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 4 – Rozdělení podle pohlaví (2019)
# ══════════════════════════════════════════════════════════════════════════
df4 = sql("""
    SELECT s.nazev, c.pohlaví, SUM(c.pocet) AS pocet
    FROM cizinec c
    JOIN stat s ON c.stat_id = s.id
    WHERE c.rok = 2019
    GROUP BY s.nazev, c.pohlaví
    ORDER BY s.nazev
""")

# ══════════════════════════════════════════════════════════════════════════
# VIZUALIZACE
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Cizinci v ČR – přehled", fontsize=16, fontweight="bold")

# ── Graf 1: Top 10 národností (horizontal bar) ─────────────────────────────
ax1 = axes[0, 0]
ax1.barh(df1["nazev"], df1["pocet"], color="steelblue")
ax1.invert_yaxis()
ax1.set_title("Top 10 národností (2019)")
ax1.set_xlabel("Počet cizinců")
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for i, v in enumerate(df1["pocet"]):
    ax1.text(v + 100, i, f"{v:,}", va="center", fontsize=8)

# ── Graf 2: Vývoj Top 5 v čase (line chart) ────────────────────────────────
ax2 = axes[0, 1]
top5 = df1["nazev"].head(5).tolist()
for nazev in top5:
    subset = df2[df2["nazev"] == nazev]
    ax2.plot(subset["rok"], subset["pocet"], marker="o", label=nazev)
ax2.set_title("Vývoj počtu cizinců – Top 5 (2017–2020)")
ax2.set_xlabel("Rok")
ax2.set_ylabel("Počet cizinců")
ax2.legend(fontsize=8)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax2.set_xticks([2017, 2018, 2019, 2020])

# ── Graf 3: Scatter cizinci vs HDP ─────────────────────────────────────────
ax3 = axes[1, 0]
sc = ax3.scatter(df3["hdp_hlava"], df3["pocet"],
                  c=df3["pocet"], cmap="YlOrRd", s=80, alpha=0.8)
for _, row in df3.iterrows():
    ax3.annotate(row["nazev"], (row["hdp_hlava"], row["pocet"]),
                  textcoords="offset points", xytext=(5, 3), fontsize=7)
ax3.set_title("Počet cizinců vs HDP na hlavu (2019)")
ax3.set_xlabel("HDP na hlavu (USD)")
ax3.set_ylabel("Počet cizinců")
ax3.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.colorbar(sc, ax=ax3, label="Počet cizinců")

# ── Graf 4: Pohlaví – stacked bar ──────────────────────────────────────────
ax4 = axes[1, 1]
df4_pivot = df4.pivot(index="nazev", columns="pohlaví", values="pocet").fillna(0)
df4_pivot = df4_pivot.sort_values("M", ascending=False)
df4_pivot.plot(kind="barh", stacked=True, ax=ax4,
               color=["steelblue", "tomato"], width=0.7)
ax4.invert_yaxis()
ax4.set_title("Rozdělení podle pohlaví (2019)")
ax4.set_xlabel("Počet cizinců")
ax4.legend(["Muži", "Ženy"])
ax4.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

plt.tight_layout()
plt.savefig("vizualizace.png", dpi=150, bbox_inches="tight")
print("\n✓ Graf uložen jako vizualizace.png")
plt.show()