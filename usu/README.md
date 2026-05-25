# IV. Úvod do strojového učení

> Cheat-sheet pro praktickou státnici. Kompletní pipeline od čištění dat po neuronové sítě.

---

## Obsah
1. [Příprava dat](#1-příprava-dat)
2. [Redukce dimenzionality – PCA, LDA](#2-redukce-dimenzionality--pca-lda)
3. [Metriky hodnocení](#3-metriky-hodnocení)
4. [Klasické algoritmy – přehled a hyperparametry](#4-klasické-algoritmy--přehled-a-hyperparametry)
5. [Pokročilé nástroje scikit-learn](#5-pokročilé-nástroje-scikit-learn)
6. [Neuronové sítě – MLP a CNN](#6-neuronové-sítě--mlp-a-cnn)
7. [Ukázková úloha – Auto MPG pipeline](#7-ukázková-úloha--auto-mpg-pipeline)

---

## 1. Příprava dat

### Načtení a první pohled
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Auto MPG dataset
url = "https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data"
cols = ["mpg","cylinders","displacement","horsepower","weight",
        "acceleration","model_year","origin","car_name"]
df = pd.read_csv(url, sep=r"\s+", names=cols, na_values="?")

print(df.shape)           # (398, 9)
print(df.dtypes)
print(df.describe())
print(df.isnull().sum())  # horsepower má 6 NaN
```

### Chybějící hodnoty
```python
# Strategie:
# - Numerické: median (robustní vůči outlierům), mean, nebo model
# - Kategorické: modus nebo vlastní kategorie "Unknown"

from sklearn.impute import SimpleImputer

imp = SimpleImputer(strategy="median")
df["horsepower"] = imp.fit_transform(df[["horsepower"]])

# Pokročilé: iterativní imputace (KNN nebo regrese)
from sklearn.impute import KNNImputer
knn_imp = KNNImputer(n_neighbors=5)
df_num = df.select_dtypes(include=np.number)
df[df_num.columns] = knn_imp.fit_transform(df_num)
```

### Odlehlé hodnoty (outliers)
```python
# IQR metoda
Q1 = df["horsepower"].quantile(0.25)
Q3 = df["horsepower"].quantile(0.75)
IQR = Q3 - Q1
maska = (df["horsepower"] >= Q1 - 1.5*IQR) & (df["horsepower"] <= Q3 + 1.5*IQR)
print(f"Outlierů: {(~maska).sum()}")
# Možnosti: odstranit, ořezat (clip), nechat (u stromů nevadí)
df["horsepower"] = df["horsepower"].clip(lower=Q1 - 1.5*IQR, upper=Q3 + 1.5*IQR)

# Vizualizace
fig, axes = plt.subplots(2, 4, figsize=(16, 6))
num_cols = ["mpg","cylinders","displacement","horsepower",
            "weight","acceleration","model_year"]
for ax, col in zip(axes.flat, num_cols):
    ax.boxplot(df[col].dropna())
    ax.set_title(col)
plt.tight_layout(); plt.show()
```

### Kategorické proměnné
```python
# origin: 1=USA, 2=Europe, 3=Japan → One-Hot Encoding
df = pd.get_dummies(df, columns=["origin"], prefix="origin", drop_first=False)
# drop_first=True → odstraní referenční kategorii (zabrání multikolinearitě)

# Ordinální encoding (když kategorie mají pořadí)
from sklearn.preprocessing import OrdinalEncoder
# df["velikost"] = OrdinalEncoder().fit_transform(df[["velikost"]])

# car_name má 300+ unikátních hodnot → zahodit nebo target encoding
df = df.drop(columns=["car_name"])
```

### Normalizace vs Standardizace
```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# StandardScaler: (x - μ) / σ → průměr=0, std=1
# Použij pro: lineární regrese, SVM, PCA, neuronové sítě
scaler_std = StandardScaler()

# MinMaxScaler: (x - min) / (max - min) → rozsah [0,1]
# Použij pro: neuronové sítě s sigmoid výstupem, KNN
scaler_mm = MinMaxScaler()

# RobustScaler: (x - median) / IQR → robustní vůči outlierům
scaler_rob = RobustScaler()

# DŮLEŽITÉ: fit pouze na trénovacích datech!
X_train_scaled = scaler_std.fit_transform(X_train)
X_test_scaled  = scaler_std.transform(X_test)   # jen transform!
```

### Analýza příznaků (Feature Importance)
```python
# Korelační matice
corr = df.corr()
plt.figure(figsize=(10,8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Korelační matice"); plt.show()

# Permutation Feature Importance (model-agnostické)
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train_scaled, y_train)

perm = permutation_importance(rf, X_test_scaled, y_test,
                               n_repeats=10, random_state=42)
feat_imp = pd.Series(perm.importances_mean, index=feature_names).sort_values()
feat_imp.plot(kind="barh", title="Permutation Feature Importance")
plt.tight_layout(); plt.show()
```

---

## 2. Redukce dimenzionality – PCA, LDA

### PCA (Principal Component Analysis)
```
Účel: nenasměrovaná redukce dimenzí (bez znalosti tříd)
Princip: najde ortogonální osy (komponenty) s maximálním rozptylem

Matematicky:
  C = (1/n) · XᵀX      ... kovarianční matice
  C·v = λ·v             ... vlastní vektory a hodnoty
  Komponenty = vlastní vektory seřazené podle λ (sestupně)
  Vysvětlená variabilita komponenty k = λₖ / Σλᵢ
```

```python
from sklearn.decomposition import PCA

# PCA před škálováním MUSÍ být data standardizována!
pca = PCA(n_components=None)   # None = všechny komponenty
pca.fit(X_train_scaled)

# Kolik komponent vysvětluje 95 % variability?
cumvar = np.cumsum(pca.explained_variance_ratio_)
n_comp = np.argmax(cumvar >= 0.95) + 1
print(f"Komponenty pro 95 % variability: {n_comp}")

# Scree plot
plt.figure(figsize=(8,4))
plt.plot(range(1, len(pca.explained_variance_ratio_)+1),
         pca.explained_variance_ratio_, "o-", label="Individuální")
plt.plot(range(1, len(cumvar)+1), cumvar, "s--", label="Kumulativní")
plt.axhline(0.95, color="red", linestyle=":", label="95 %")
plt.xlabel("Komponenta"); plt.ylabel("Vysvětlená variabilita")
plt.title("PCA – Scree plot"); plt.legend(); plt.show()

# Aplikace PCA s vybraným počtem komponent
pca_final = PCA(n_components=n_comp)
X_train_pca = pca_final.fit_transform(X_train_scaled)
X_test_pca  = pca_final.transform(X_test_scaled)
```

### LDA (Linear Discriminant Analysis)
```
Účel: nasměrovaná redukce dimenzí (používá informaci o třídách)
→ Maximalizuje poměr variability MEZI třídami / UVNITŘ tříd
→ Vhodné pro klasifikaci, ne regresi
→ Max. komponent = min(počet_tříd - 1, počet_příznaků)
```

```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# LDA pro klasifikaci (origin: USA/Europe/Japan)
lda = LinearDiscriminantAnalysis(n_components=2)
X_train_lda = lda.fit_transform(X_train_scaled, y_train_cat)
X_test_lda  = lda.transform(X_test_scaled)

# Vizualizace 2D projekce
plt.scatter(X_train_lda[:,0], X_train_lda[:,1],
            c=y_train_cat, cmap="Set1", alpha=0.6)
plt.xlabel("LD1"); plt.ylabel("LD2")
plt.title("LDA projekce (origin)"); plt.colorbar(); plt.show()
```

---

## 3. Metriky hodnocení

### Regresní metriky
```
MAE  = (1/n) · Σ|yᵢ - ŷᵢ|          ... průměrná absolutní chyba (stejné jednotky jako Y)
MSE  = (1/n) · Σ(yᵢ - ŷᵢ)²         ... citlivé na velké chyby (outliers)
RMSE = √MSE                           ... jako MAE ale penalizuje větší chyby
R²   = 1 - SS_res/SS_tot              ... 0–1, % vysvětlené variability
```

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def evaluate_regression(y_true, y_pred, name="Model"):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    print(f"{name:25s} | MAE={mae:.3f} | RMSE={rmse:.3f} | R²={r2:.4f}")
    return {"model": name, "MAE": mae, "RMSE": rmse, "R2": r2}
```

### Klasifikační metriky
```
               Předpovězeno+   Předpovězeno-
Skutečnost+  |      TP       |      FN      |  ← Sensitivity = TP/(TP+FN)
Skutečnost-  |      FP       |      TN      |  ← Specificity = TN/(TN+FP)

Accuracy    = (TP + TN) / (TP + TN + FP + FN)
Precision   = TP / (TP + FP)       ... z předpovězených +, kolik bylo správně
Recall      = TP / (TP + FN)       ... ze všech +, kolik jsme odhalili (= Sensitivity)
F1-score    = 2 · (Precision · Recall) / (Precision + Recall)   ... harmonický průměr

→ Accuracy klamná při nevyvážených třídách!
→ F1 lepší pro nevyvážené třídy
→ AUC-ROC pro celkový výkon bez ohledu na threshold
```

```python
from sklearn.metrics import (classification_report, confusion_matrix,
                               ConfusionMatrixDisplay, roc_auc_score)

y_pred = model.predict(X_test)

# Matice záměn
cm = confusion_matrix(y_test, y_pred)
ConfusionMatrixDisplay(cm, display_labels=model.classes_).plot(cmap="Blues")
plt.title("Matice záměn"); plt.show()

# Kompletní report
print(classification_report(y_test, y_pred,
      target_names=["USA","Europe","Japan"]))
#               precision  recall  f1-score  support
# USA               0.87    0.91      0.89       55
# Europe            0.78    0.72      0.75       25
# ...

# AUC (pro binární nebo one-vs-rest)
auc = roc_auc_score(y_test, model.predict_proba(X_test), multi_class="ovr")
print(f"AUC-ROC (OvR): {auc:.4f}")
```

---

## 4. Klasické algoritmy – přehled a hyperparametry

### Přehledová tabulka
| Algoritmus | Typ | Škálování nutné? | Klíčové hyperparametry |
|-----------|-----|-----------------|----------------------|
| Linear/Ridge Regression | reg | ANO | `alpha` (regularizace) |
| Logistic Regression | klas | ANO | `C`, `penalty` |
| Decision Tree | reg/klas | NE | `max_depth`, `min_samples_split` |
| Random Forest | reg/klas | NE | `n_estimators`, `max_depth`, `max_features` |
| SVR / SVC | reg/klas | ANO | `C`, `kernel`, `gamma`, `epsilon` |
| KNN | reg/klas | ANO | `n_neighbors`, `weights` |
| Gradient Boosting | reg/klas | NE | `n_estimators`, `learning_rate`, `max_depth` |

---

### Rozhodovací stromy
```
Princip: rekurzivní dělení prostoru příznaků
Kritérium dělení:
  - Regrese: MSE nebo MAE
  - Klasifikace: Gini impurity nebo Entropie (Information Gain)

Gini = 1 - Σ pₖ²      (pravděpodobnost nesprávné klasifikace)
Entropie = -Σ pₖ·log₂(pₖ)

Hyperparametry:
  max_depth        → hloubka stromu (overfitting při velké hloubce)
  min_samples_split → min. vzorků pro rozdělení uzlu
  min_samples_leaf  → min. vzorků v listu
  ccp_alpha         → cost-complexity pruning (ořezání)
```

```python
from sklearn.tree import DecisionTreeRegressor, export_text, plot_tree

dt = DecisionTreeRegressor(max_depth=4, min_samples_split=10, random_state=42)
dt.fit(X_train_scaled, y_train)

# Vizualizace stromu
plt.figure(figsize=(20, 8))
plot_tree(dt, feature_names=feature_names, filled=True, rounded=True)
plt.show()

# Textový výpis
print(export_text(dt, feature_names=feature_names))
```

### Random Forest
```
Princip: bagging (bootstrap + averaging) M rozhodovacích stromů
  - Každý strom trénován na bootstrap vzorku (sampling WITH replacement)
  - Každé dělení používá jen náhodnou podmnožinu příznaků (√p nebo log₂p)
  - Predikce = průměr (regrese) nebo majority vote (klasifikace)

Výhody: robustní vůči overfittingu, feature importance, žádné škálování
```

```python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

rf = RandomForestRegressor(
    n_estimators=200,    # počet stromů (víc = lepší, ale pomalejší)
    max_depth=None,      # None = plné stromy
    max_features="sqrt", # "sqrt", "log2", nebo číslo
    min_samples_leaf=2,
    n_jobs=-1,           # paralelizace
    random_state=42
)
rf.fit(X_train_scaled, y_train)

# Feature importance (ze stromu, ne permutační)
importances = pd.Series(rf.feature_importances_, index=feature_names)
importances.sort_values().plot(kind="barh", title="RF Feature Importance")
plt.show()
```

### SVM / SVR
```
Princip (SVC): hledá hyperrovinu s maximální marginí mezi třídami
  Marginа = 2/||w||, maximalizujeme → minimalizujeme ||w||²

Kernel trick: transformuje data do vyššího dimenzionálního prostoru
  Linear:  K(x,z) = xᵀz
  RBF:     K(x,z) = exp(-γ·||x-z||²)   ← nejčastější
  Poly:    K(x,z) = (xᵀz + r)^d

Hyperparametry:
  C     → penalizace za chybu (malé C = větší margin + více chyb, velké C = malý margin + méně chyb)
  gamma → šířka RBF jádra (malé γ = hladká hranice, velké γ = komplexní hranice)
  epsilon → (SVR) šířka "tube" kolem regresní funkce, kde se nechybuje
```

```python
from sklearn.svm import SVR, SVC

svr = SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.5)
svr.fit(X_train_scaled, y_train)
y_pred_svr = svr.predict(X_test_scaled)
```

### Logistická regrese (sklearn)
```
Regularizace:
  L1 (Lasso):  penalizuje Σ|βⱼ|   → řídká řešení (některé β=0), výběr příznaků
  L2 (Ridge):  penalizuje Σβⱼ²    → malé koeficienty, neodstraňuje příznaky
  ElasticNet:  kombinace L1 + L2

  C = 1/λ → malé C = silná regularizace
```

```python
from sklearn.linear_model import LogisticRegression, Ridge, Lasso

# Klasifikace
lr = LogisticRegression(C=1.0, penalty="l2", solver="lbfgs",
                         max_iter=1000, multi_class="auto")
lr.fit(X_train_scaled, y_train)

# Regrese s regularizací
ridge = Ridge(alpha=1.0)           # alpha = λ (penalizace)
lasso = Lasso(alpha=0.1)
ridge.fit(X_train_scaled, y_train)
```

---

## 5. Pokročilé nástroje scikit-learn

### Train-test split + Cross-validation
```python
from sklearn.model_selection import (train_test_split, cross_val_score,
                                      KFold, StratifiedKFold, GridSearchCV,
                                      RandomizedSearchCV)

# Základní split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# K-Fold cross-validace (k=5 nebo 10 je standard)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(rf, X_scaled, y, cv=kf, scoring="r2", n_jobs=-1)
print(f"CV R² = {scores.mean():.4f} ± {scores.std():.4f}")

# StratifiedKFold (pro klasifikaci – zachovává poměr tříd)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

### Pipeline
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

# Pipeline automaticky aplikuje transformace správně (fit na train, transform na test)
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("pca",    PCA(n_components=5)),    # volitelný krok
    ("model",  RandomForestRegressor(n_estimators=100, random_state=42))
])

pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)

# Pipeline lze přímo předat do GridSearchCV
```

### Hledání hyperparametrů
```python
# GridSearchCV – prochází všechny kombinace (vhodné pro malý prostor)
param_grid = {
    "model__n_estimators": [50, 100, 200],
    "model__max_depth":    [None, 5, 10],
    "model__max_features": ["sqrt", "log2"]
}
# → 3 × 3 × 2 = 18 kombinací × 5 foldů = 90 fitů

grid = GridSearchCV(pipe, param_grid, cv=5, scoring="r2",
                    n_jobs=-1, verbose=1, refit=True)
grid.fit(X_train, y_train)

print(f"Nejlepší parametry: {grid.best_params_}")
print(f"Nejlepší CV R²:     {grid.best_score_:.4f}")
y_pred_best = grid.predict(X_test)

# RandomizedSearchCV – náhodné vzorkování (pro velký prostor)
from scipy.stats import randint, uniform
param_dist = {
    "model__n_estimators": randint(50, 500),
    "model__max_depth":    [None, 3, 5, 10, 15],
    "model__max_features": ["sqrt", "log2", 0.5]
}
rnd = RandomizedSearchCV(pipe, param_dist, n_iter=30, cv=5,
                          scoring="r2", n_jobs=-1, random_state=42)
rnd.fit(X_train, y_train)
print(f"Nejlepší parametry: {rnd.best_params_}")
```

### Výsledky GridSearch jako DataFrame
```python
cv_results = pd.DataFrame(grid.cv_results_)
cv_results[["params","mean_test_score","std_test_score","rank_test_score"]] \
    .sort_values("rank_test_score").head(10)
```

---

## 6. Neuronové sítě – MLP a CNN

### MLP (Multilayer Perceptron) – matematika
```
Vstupní vrstva: x = [x₁, x₂, ..., xₙ]

Skrytá vrstva l:
  z^(l) = W^(l) · a^(l-1) + b^(l)    ... lineární kombinace
  a^(l) = f(z^(l))                    ... aktivační funkce

Aktivační funkce:
  ReLU:    f(x) = max(0, x)            → defaultní pro skryté vrstvy
  Sigmoid: f(x) = 1/(1+e⁻ˣ)          → binární klasifikace (výstupní vrstva)
  Softmax: f(xₖ) = eˣᵏ / Σeˣⱼ        → multi-class klasifikace (výstup)
  Linear:  f(x) = x                   → regrese (výstupní vrstva)
  Tanh:    f(x) = (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) → [-1,1], alternativa k sigmoid

Loss funkce:
  Regrese:      MSE = (1/n)Σ(y-ŷ)²
  Binarní klas: BCE = -Σ[y·log(ŷ) + (1-y)·log(1-ŷ)]
  Multi-class:  CCE = -Σ yₖ·log(ŷₖ)

Trénink – Backpropagation + Gradient Descent:
  ∂L/∂W = backpropagation (chain rule)
  W ← W - η · ∂L/∂W     (η = learning rate)
  Optimizer Adam: adaptivní learning rate per parametr
```

### MLP v Keras
```python
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Normalizace nutná!
# X_train_scaled, X_test_scaled ze StandardScaler

def build_mlp(n_features, hidden_layers=[64, 32], dropout=0.2,
               activation="relu", learning_rate=1e-3):
    model = keras.Sequential(name="MLP_regressor")
    model.add(layers.Input(shape=(n_features,)))

    for units in hidden_layers:
        model.add(layers.Dense(units, activation=activation))
        model.add(layers.BatchNormalization())   # stabilizace tréniku
        model.add(layers.Dropout(dropout))       # regularizace (zabraňuje overfittingu)

    model.add(layers.Dense(1, activation="linear"))  # regresní výstup

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="mse",
        metrics=["mae"]
    )
    return model

model_mlp = build_mlp(n_features=X_train_scaled.shape[1])
model_mlp.summary()
```
```
Model: "MLP_regressor"
┌──────────────────┬─────────────┬───────────┐
│ Layer (type)     │ Output Shape│   Param # │
├──────────────────┼─────────────┼───────────┤
│ dense (Dense)    │ (None, 64)  │       448 │
│ dropout          │ (None, 64)  │         0 │
│ dense_1 (Dense)  │ (None, 32)  │     2,080 │
│ dropout_1        │ (None, 32)  │         0 │
│ dense_2 (Dense)  │ (None, 1)   │        33 │
└──────────────────┴─────────────┴───────────┘
 Total params: 2,561
```

```python
# Trénink
early_stop = keras.callbacks.EarlyStopping(
    monitor="val_loss", patience=20, restore_best_weights=True
)
history = model_mlp.fit(
    X_train_scaled, y_train,
    validation_split=0.2,
    epochs=200,
    batch_size=32,
    callbacks=[early_stop],
    verbose=0
)

# Learning curves
plt.figure(figsize=(10,4))
plt.subplot(1,2,1)
plt.plot(history.history["loss"], label="Train loss")
plt.plot(history.history["val_loss"], label="Val loss")
plt.xlabel("Epoch"); plt.ylabel("MSE"); plt.legend()
plt.title("Learning curve – Loss")

plt.subplot(1,2,2)
plt.plot(history.history["mae"], label="Train MAE")
plt.plot(history.history["val_mae"], label="Val MAE")
plt.xlabel("Epoch"); plt.ylabel("MAE"); plt.legend()
plt.title("Learning curve – MAE")
plt.tight_layout(); plt.show()

# Evaluace
y_pred_mlp = model_mlp.predict(X_test_scaled).flatten()
```

### Optimalizace hyperparametrů MLP (Keras Tuner)
```python
import keras_tuner as kt

def build_tunable(hp):
    n_layers = hp.Int("n_layers", 1, 4)
    units    = hp.Choice("units", [16, 32, 64, 128])
    dropout  = hp.Float("dropout", 0.0, 0.5, step=0.1)
    lr       = hp.Choice("lr", [1e-2, 1e-3, 1e-4])

    model = keras.Sequential()
    model.add(layers.Input(shape=(X_train_scaled.shape[1],)))
    for _ in range(n_layers):
        model.add(layers.Dense(units, activation="relu"))
        model.add(layers.Dropout(dropout))
    model.add(layers.Dense(1))
    model.compile(optimizer=keras.optimizers.Adam(lr), loss="mse", metrics=["mae"])
    return model

tuner = kt.RandomSearch(build_tunable, objective="val_mae",
                         max_trials=20, directory="tuning", project_name="mlp")
tuner.search(X_train_scaled, y_train, epochs=100,
             validation_split=0.2, callbacks=[early_stop], verbose=0)
best_hp = tuner.get_best_hyperparameters()[0]
print(best_hp.values)
```

### CNN – základní princip (pro kontext)
```
Konvoluční vrstva: aplikuje filtry (kernely) na vstup
  Výstup = vstup ⊗ kernel + bias
  Detekuje lokální vzory (hrany, textury v obrazech)

Pooling vrstva: redukuje prostorové dimenze
  Max pooling: bere maximum z oblasti → nejsilnější příznak

Typická architektura pro obrazy:
  Input → [Conv2D → ReLU → MaxPool] × N → Flatten → Dense → Output

Pro tabulková data CNN obvykle NEPŘEKONÁVÁ MLP nebo stromy!
```

```python
# CNN pro 1D signály (pokud by data byla časová řada)
from tensorflow.keras import layers, models

cnn_1d = models.Sequential([
    layers.Input(shape=(n_timesteps, n_features)),
    layers.Conv1D(32, kernel_size=3, activation="relu"),
    layers.MaxPooling1D(pool_size=2),
    layers.Conv1D(64, kernel_size=3, activation="relu"),
    layers.GlobalAveragePooling1D(),
    layers.Dense(32, activation="relu"),
    layers.Dense(1)
])
```

---

## 7. Ukázková úloha – Auto MPG pipeline

### Kompletní workflow
```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

# --- 1. Načtení ---
url = "https://archive.ics.uci.edu/ml/machine-learning-databases/auto-mpg/auto-mpg.data"
cols = ["mpg","cylinders","displacement","horsepower","weight",
        "acceleration","model_year","origin","car_name"]
df = pd.read_csv(url, sep=r"\s+", names=cols, na_values="?")

# --- 2. Čištění ---
df["horsepower"] = df["horsepower"].fillna(df["horsepower"].median())
df = pd.get_dummies(df, columns=["origin"], drop_first=True)
df = df.drop(columns=["car_name"])

# --- 3. Split ---
X = df.drop(columns=["mpg"])
y = df["mpg"]
feature_names = X.columns.tolist()
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# --- 4. Modely ---
modely = {
    "Ridge": Pipeline([
        ("scaler", StandardScaler()),
        ("model", Ridge(alpha=1.0))
    ]),
    "SVR_rbf": Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVR(kernel="rbf", C=10, gamma="scale", epsilon=0.5))
    ]),
    "RandomForest": Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(n_estimators=200, max_depth=None,
                                         random_state=42, n_jobs=-1))
    ]),
    "GradientBoosting": Pipeline([
        ("scaler", StandardScaler()),
        ("model", GradientBoostingRegressor(n_estimators=200,
                                             learning_rate=0.05,
                                             max_depth=4, random_state=42))
    ])
}

# --- 5. Evaluace ---
results = []
for nazev, pipe in modely.items():
    cv_r2 = cross_val_score(pipe, X_train, y_train, cv=5,
                             scoring="r2", n_jobs=-1).mean()
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    results.append({
        "Model":    nazev,
        "CV R²":    round(cv_r2, 4),
        "Test R²":  round(r2_score(y_test, y_pred), 4),
        "Test MAE": round(mean_absolute_error(y_test, y_pred), 3),
        "Test RMSE":round(np.sqrt(np.mean((y_test-y_pred)**2)), 3)
    })

df_res = pd.DataFrame(results).sort_values("Test R²", ascending=False)
print(df_res.to_string(index=False))
```
```
Model              CV R²   Test R²  Test MAE  Test RMSE
GradientBoosting   0.8923   0.9012    1.823     2.431
RandomForest       0.8845   0.8934    1.891     2.515
SVR_rbf            0.8612   0.8753    2.012     2.721
Ridge              0.8021   0.8134    2.543     3.312
```

### Vizualizace porovnání modelů
```python
# Predicted vs Actual pro nejlepší model
best_pipe = modely["GradientBoosting"]
y_pred_best = best_pipe.predict(X_test)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].scatter(y_test, y_pred_best, alpha=0.6, color="steelblue")
axes[0].plot([y_test.min(), y_test.max()],
             [y_test.min(), y_test.max()], "r--", lw=2)
axes[0].set(xlabel="Skutečné MPG", ylabel="Předpovězené MPG",
            title="Gradient Boosting – Predicted vs Actual")

residuals = y_test - y_pred_best
axes[1].scatter(y_pred_best, residuals, alpha=0.6, color="tomato")
axes[1].axhline(0, color="black", linestyle="--")
axes[1].set(xlabel="Předpovězené MPG", ylabel="Reziduál",
            title="Residuály")

plt.tight_layout(); plt.show()

# Srovnávací bar chart
df_res_plot = df_res.set_index("Model")
df_res_plot[["Test R²"]].plot(kind="bar", figsize=(8,4),
                               title="Porovnání modelů – R²",
                               color="steelblue", legend=False)
plt.xticks(rotation=20); plt.ylabel("R²"); plt.ylim(0.7, 1.0)
plt.tight_layout(); plt.show()
```

### MLP pro Auto MPG
```python
from tensorflow import keras
from tensorflow.keras import layers

scaler = StandardScaler()
X_tr = scaler.fit_transform(X_train)
X_te = scaler.transform(X_test)

mlp = keras.Sequential([
    layers.Input(shape=(X_tr.shape[1],)),
    layers.Dense(64, activation="relu"),
    layers.Dropout(0.2),
    layers.Dense(32, activation="relu"),
    layers.Dropout(0.2),
    layers.Dense(1)
])
mlp.compile(optimizer="adam", loss="mse", metrics=["mae"])

es = keras.callbacks.EarlyStopping(patience=20, restore_best_weights=True)
mlp.fit(X_tr, y_train, validation_split=0.2,
        epochs=200, batch_size=16, callbacks=[es], verbose=0)

y_pred_mlp = mlp.predict(X_te).flatten()
print(f"MLP → R²={r2_score(y_test,y_pred_mlp):.4f}, "
      f"MAE={mean_absolute_error(y_test,y_pred_mlp):.3f}")
# MLP → R²=0.8821, MAE=1.956
```

### Závěrečná tabulka (přidat MLP)
```python
mlp_row = {
    "Model": "MLP",
    "CV R²": "N/A",
    "Test R²":  round(r2_score(y_test, y_pred_mlp), 4),
    "Test MAE": round(mean_absolute_error(y_test, y_pred_mlp), 3),
    "Test RMSE":round(np.sqrt(np.mean((y_test-y_pred_mlp)**2)), 3)
}
df_final = pd.concat([df_res, pd.DataFrame([mlp_row])], ignore_index=True)
print(df_final.to_string(index=False))
```

---

*Aktualizováno pro státnici – Python (scikit-learn, Keras/TensorFlow, pandas, matplotlib)*