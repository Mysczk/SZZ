"""
Dotazy a vizualizace nad MongoDB.
Spusť až po mongo_load.py.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pymongo import MongoClient

# ── Připojení ──────────────────────────────────────────────────────────────
client = MongoClient("mongodb://localhost:27017/")
db     = client["szz"]
col    = db["staty"]

# ── Helper ─────────────────────────────────────────────────────────────────
def agg(pipeline):
    return list(col.aggregate(pipeline))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 1 – Top 10 národností v roce 2019
# ══════════════════════════════════════════════════════════════════════════
top10 = agg([
    {"$unwind": "$cizinci"},
    {"$match": {"cizinci.rok": 2019}},
    {"$group": {
        "_id":    "$_id",
        "nazev":  {"$first": "$nazev"},
        "celkem": {"$sum": "$cizinci.pocet"}
    }},
    {"$sort": {"celkem": -1}},
    {"$limit": 10}
])
df1 = pd.DataFrame(top10).rename(columns={"_id": "kod", "celkem": "pocet"})
print("── Top 10 národností (2019) ──")
print(df1[["nazev", "pocet"]].to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 2 – Vývoj Top 5 v letech
# ══════════════════════════════════════════════════════════════════════════
vyvoj = agg([
    {"$unwind": "$cizinci"},
    {"$group": {
        "_id":    {"kod": "$_id", "rok": "$cizinci.rok"},
        "nazev":  {"$first": "$nazev"},
        "celkem": {"$sum": "$cizinci.pocet"}
    }},
    {"$sort": {"_id.rok": 1, "celkem": -1}}
])
df2 = pd.DataFrame([{
    "nazev":  r["nazev"],
    "rok":    r["_id"]["rok"],
    "pocet":  r["celkem"]
} for r in vyvoj])

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 3 – Cizinci vs HDP (2019) + kategorie
# ══════════════════════════════════════════════════════════════════════════
hdp_kat = agg([
    {"$unwind": "$cizinci"},
    {"$unwind": "$hdp"},
    {"$match": {
        "$expr": {"$eq": ["$cizinci.rok", "$hdp.rok"]},
        "cizinci.rok": 2019
    }},
    {"$addFields": {
        "hdp_kategorie": {
            "$switch": {
                "branches": [
                    {"case": {"$lt": ["$hdp.hdp_hlava", 5000]},
                     "then": "Nízký (<5k)"},
                    {"case": {"$lt": ["$hdp.hdp_hlava", 20000]},
                     "then": "Střední (5k–20k)"},
                ],
                "default": "Vysoký (>20k)"
            }
        }
    }},
    {"$group": {
        "_id":           "$hdp_kategorie",
        "pocet_cizincu": {"$sum": "$cizinci.pocet"},
        "pocet_statu":   {"$addToSet": "$_id"}
    }},
    {"$addFields": {"pocet_statu": {"$size": "$pocet_statu"}}},
    {"$sort": {"pocet_cizincu": -1}}
])
df3 = pd.DataFrame(hdp_kat).rename(columns={"_id": "kategorie"})
print("\n── Cizinci podle HDP kategorie (2019) ──")
print(df3[["kategorie", "pocet_cizincu", "pocet_statu"]].to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════
# DOTAZ 4 – Scatter: cizinci vs HDP na hlavu
# ══════════════════════════════════════════════════════════════════════════
scatter = agg([
    {"$unwind": "$cizinci"},
    {"$unwind": "$hdp"},
    {"$match": {
        "$expr": {"$eq": ["$cizinci.rok", "$hdp.rok"]},
        "cizinci.rok": 2019
    }},
    {"$group": {
        "_id":       "$_id",
        "nazev":     {"$first": "$nazev"},
        "pocet":     {"$sum": "$cizinci.pocet"},
        "hdp_hlava": {"$first": "$hdp.hdp_hlava"}
    }}
])
df4 = pd.DataFrame(scatter)

# ══════════════════════════════════════════════════════════════════════════
# VIZUALIZACE
# ══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Cizinci v ČR – MongoDB analýza", fontsize=16, fontweight="bold")

# ── Graf 1: Top 10 bar ─────────────────────────────────────────────────────
ax1 = axes[0, 0]
ax1.barh(df1["nazev"], df1["pocet"], color="steelblue")
ax1.invert_yaxis()
ax1.set_title("Top 10 národností (2019)")
ax1.set_xlabel("Počet cizinců")
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for i, v in enumerate(df1["pocet"]):
    ax1.text(v + 100, i, f"{v:,}", va="center", fontsize=8)

# ── Graf 2: Vývoj Top 5 line chart ────────────────────────────────────────
ax2 = axes[0, 1]
top5_nazvy = df1["nazev"].head(5).tolist()
for nazev in top5_nazvy:
    subset = df2[df2["nazev"] == nazev].sort_values("rok")
    ax2.plot(subset["rok"], subset["pocet"], marker="o", label=nazev)
ax2.set_title("Vývoj počtu cizinců – Top 5 (2017–2020)")
ax2.set_xlabel("Rok")
ax2.set_ylabel("Počet")
ax2.legend(fontsize=8)
ax2.set_xticks([2017, 2018, 2019, 2020])
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# ── Graf 3: HDP kategorie bar ──────────────────────────────────────────────
ax3 = axes[1, 0]
barvy = {"Vysoký (>20k)": "steelblue",
         "Střední (5k–20k)": "orange",
         "Nízký (<5k)": "tomato"}
colors = [barvy.get(k, "gray") for k in df3["kategorie"]]
ax3.bar(df3["kategorie"], df3["pocet_cizincu"], color=colors)
ax3.set_title("Cizinci podle HDP kategorie státu (2019)")
ax3.set_ylabel("Počet cizinců")
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for i, (v, s) in enumerate(zip(df3["pocet_cizincu"], df3["pocet_statu"])):
    ax3.text(i, v + 500, f"{v:,}\n({s} států)", ha="center", fontsize=8)

# ── Graf 4: Scatter cizinci vs HDP ────────────────────────────────────────
ax4 = axes[1, 1]
sc = ax4.scatter(df4["hdp_hlava"], df4["pocet"],
                  c=df4["pocet"], cmap="YlOrRd", s=80, alpha=0.8)
for _, row in df4.iterrows():
    ax4.annotate(row["nazev"], (row["hdp_hlava"], row["pocet"]),
                  textcoords="offset points", xytext=(5, 3), fontsize=7)
ax4.set_title("Počet cizinců vs HDP na hlavu (2019)")
ax4.set_xlabel("HDP na hlavu (USD)")
ax4.set_ylabel("Počet cizinců")
ax4.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.colorbar(sc, ax=ax4, label="Počet cizinců")

plt.tight_layout()
plt.savefig("mongo_vizualizace.png", dpi=150, bbox_inches="tight")
print("\n✓ Graf uložen jako mongo_vizualizace.png")
plt.show()