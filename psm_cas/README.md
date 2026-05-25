# III. Pokročilé statistické metody a zpracování časových řad

> Cheat-sheet pro praktickou státnici. Důraz na matematické formulace, interpretaci a Python kód.

---

## Obsah
1. [Jednoduchá lineární regrese](#1-jednoduchá-lineární-regrese)
2. [Mnohonásobná lineární regrese](#2-mnohonásobná-lineární-regrese)
3. [Nelineární regresní modely](#3-nelineární-regresní-modely)
4. [Analýza rozptylu (ANOVA)](#4-analýza-rozptylu-anova)
5. [Logistická regrese](#5-logistická-regrese)
6. [Předpoklady regresních modelů & nápravné kroky](#6-předpoklady-regresních-modelů--nápravné-kroky)
7. [Dekompozice časových řad](#7-dekompozice-časových-řad)
8. [Box-Jenkinsova metodologie: ARMA, ARIMA, SARIMA](#8-box-jenkinsova-metodologie-arma-arima-sarima)
9. [Dynamické lineární modely (VAR, CCF)](#9-dynamické-lineární-modely-var-ccf)
10. [Postup pro ukázkovou úlohu](#10-postup-pro-ukázkovou-úlohu)

---

## 1. Jednoduchá lineární regrese

### Matematická formulace
```
Y_i = β₀ + β₁·X_i + ε_i

kde:
  Y_i  ... závislá proměnná (výška hladiny)
  X_i  ... nezávislá proměnná (srážky, průtok, ...)
  β₀   ... intercept (hodnota Y když X=0)
  β₁   ... slope (o kolik vzroste Y, když X vzroste o 1)
  ε_i  ... reziduál ~ N(0, σ²)
```

**Odhad metodou nejmenších čtverců (OLS):**
```
β̂₁ = Σ(Xᵢ - X̄)(Yᵢ - Ȳ) / Σ(Xᵢ - X̄)²
β̂₀ = Ȳ - β̂₁·X̄
```

**Kvalita modelu:**
```
R² = 1 - SS_res / SS_tot = vysvětlená variabilita (0–1)
SS_res = Σ(Yᵢ - Ŷᵢ)²   ... reziduální součet čtverců
SS_tot = Σ(Yᵢ - Ȳ)²    ... celkový součet čtverců
RMSE = √(SS_res / n)    ... střední chyba reziduí
```

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

df = pd.read_csv("reka.csv")

# OLS přes statsmodels (dává plný výpis!)
X = sm.add_constant(df["srazky"])   # přidá intercept β₀
model = sm.OLS(df["hladina"], X).fit()
print(model.summary())
```
```
OLS Regression Results
=======================
R-squared:       0.743
Adj. R-squared:  0.741
F-statistic:     412.3  (p < 0.001 → model je signifikantní)
-------------------------
             coef   std err    t      P>|t|
const       12.45    1.23    10.12   0.000   ← intercept
srazky       0.87    0.04    21.74   0.000   ← slope
```

**Interpretace β₁ = 0.87:**
> „Každé zvýšení srážek o 1 mm odpovídá průměrnému zvýšení hladiny o 0.87 cm,
> za předpokladu ostatních faktorů konstantních."

---

## 2. Mnohonásobná lineární regrese

### Matematická formulace
```
Y = β₀ + β₁X₁ + β₂X₂ + ... + βₖXₖ + ε

Maticově: Y = Xβ + ε
Odhad OLS: β̂ = (XᵀX)⁻¹ Xᵀ Y
```

**Upravený R² (penalizuje za počet proměnných):**
```
R²_adj = 1 - (1 - R²) · (n-1)/(n-k-1)

kde k = počet prediktorů, n = počet pozorování
→ R²_adj klesne, pokud přidáme bezvýznamný prediktor
```

**Informační kritéria (čím nižší, tím lepší model):**
```
AIC = 2k - 2·ln(L)          ... Akaikeho kritérium
BIC = k·ln(n) - 2·ln(L)     ... Bayesovské (tvrdší penalizace)

kde L = likelihood modelu, k = počet parametrů
→ BIC více trestá složité modely
```

```python
# Mnohonásobná regrese
cols = ["srazky", "teplota", "prietok", "tlak"]
X = sm.add_constant(df[cols])
model_multi = sm.OLS(df["hladina"], X).fit()
print(model_multi.summary())

# Stepwise selection (kroková regrese) – sklearn alternativa
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import SequentialFeatureSelector

lr = LinearRegression()
sfs = SequentialFeatureSelector(lr, n_features_to_select="auto",
                                 direction="forward", scoring="r2")
sfs.fit(df[cols], df["hladina"])
print("Vybrané proměnné:", np.array(cols)[sfs.get_support()])
```

**Multikolinearita – VIF:**
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif = pd.DataFrame({
    "feature": cols,
    "VIF": [variance_inflation_factor(df[cols].values, i) for i in range(len(cols))]
})
print(vif)
# VIF > 10 → problém s multikolinearitou → zvažit odstranění proměnné
```

**Interakce:**
```python
# β₃·(X₁·X₂) – efekt X₁ závisí na hodnotě X₂
df["srazky_x_teplota"] = df["srazky"] * df["teplota"]
X_interakce = sm.add_constant(df[["srazky","teplota","srazky_x_teplota"]])
model_int = sm.OLS(df["hladina"], X_interakce).fit()
```

---

## 3. Nelineární regresní modely

### Polynomická regrese
```
Y = β₀ + β₁X + β₂X² + β₃X³ + ε

→ Stále je to lineární model v parametrech β!
→ OLS odhad funguje stejně, jen přidáme sloupce X², X³, ...
```

```python
from sklearn.preprocessing import PolynomialFeatures

poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(df[["srazky"]])
X_poly_const = sm.add_constant(X_poly)
model_poly = sm.OLS(df["hladina"], X_poly_const).fit()
print(model_poly.summary())

# Vizualizace
x_range = np.linspace(df["srazky"].min(), df["srazky"].max(), 300)
x_pred  = sm.add_constant(poly.transform(x_range.reshape(-1,1)))
y_pred  = model_poly.predict(x_pred)

plt.scatter(df["srazky"], df["hladina"], alpha=0.4, label="Data")
plt.plot(x_range, y_pred, color="red", label="Polynomická regrese (deg=2)")
plt.legend(); plt.show()
```

### Logaritmická transformace (při nestabilním rozptylu)
```
ln(Y) = β₀ + β₁X + ε
→ Interpretace β₁: zvýšení X o 1 → změna Y o (e^β₁ - 1) · 100 %
```

```python
df["log_hladina"] = np.log(df["hladina"])
model_log = sm.OLS(df["log_hladina"], sm.add_constant(df["srazky"])).fit()
```

### Skutečně nelineární model (scipy curve_fit)
```python
from scipy.optimize import curve_fit

def exponencialni(x, a, b, c):
    return a * np.exp(b * x) + c

popt, pcov = curve_fit(exponencialni, df["srazky"], df["hladina"],
                        p0=[1, 0.01, 0], maxfev=5000)
print(f"a={popt[0]:.3f}, b={popt[1]:.3f}, c={popt[2]:.3f}")
```

---

## 4. Analýza rozptylu (ANOVA)

### Jednofaktorová ANOVA
```
Hypotéza: H₀: μ₁ = μ₂ = ... = μₖ  (všechny skupinové průměry jsou stejné)
          H₁: alespoň jeden průměr se liší

F = (SS_between / df_between) / (SS_within / df_within)
  = MS_between / MS_within

kde:
  SS_between = Σ nⱼ·(Ȳⱼ - Ȳ)²    ... variabilita MEZI skupinami
  SS_within  = ΣΣ (Yᵢⱼ - Ȳⱼ)²   ... variabilita UVNITŘ skupin
  df_between = k - 1
  df_within  = N - k
```

```python
from scipy.stats import f_oneway

# Skupiny: výška hladiny v různých ročních obdobích
jaro  = df[df["rocni_obdobi"]=="jaro"]["hladina"]
leto  = df[df["rocni_obdobi"]=="leto"]["hladina"]
podzim= df[df["rocni_obdobi"]=="podzim"]["hladina"]
zima  = df[df["rocni_obdobi"]=="zima"]["hladina"]

F, p = f_oneway(jaro, leto, podzim, zima)
print(f"F = {F:.3f}, p = {p:.4f}")
# p < 0.05 → zamítáme H₀ → průměry se statisticky liší

# Post-hoc test (které dvojice se liší)
from statsmodels.stats.multicomp import pairwise_tukeyhsd
tukey = pairwise_tukeyhsd(df["hladina"], df["rocni_obdobi"])
print(tukey.summary())
```

---

## 5. Logistická regrese

### Matematická formulace
```
Používá se, když Y je binární (0/1), např.: povodeň / bez povodně

P(Y=1 | X) = 1 / (1 + e^(-(β₀ + β₁X₁ + ... + βₖXₖ)))
            = σ(Xβ)   ... sigmoid funkce

Logit transformace (linearizace):
  ln( P/(1-P) ) = β₀ + β₁X₁ + ... + βₖXₖ
  → levá strana = log-odds (logaritmus šance)

Odhad: Maximum Likelihood (ne OLS!)
  L(β) = Π P(Yᵢ|Xᵢ)   → maximalizujeme log L
```

**Interpretace koeficientů:**
```
Odds ratio = e^βⱼ
→ zvýšení Xⱼ o 1 jednotku násobí šanci jevu (P/(1-P)) faktorem e^βⱼ

Příklad: β₁ = 0.15 pro srážky
→ OR = e^0.15 = 1.162
→ každý mm srážek navíc zvyšuje šanci povodně o 16.2 %
```

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, RocCurveDisplay
from sklearn.model_selection import train_test_split

# Binární cílová proměnná
df["povoden"] = (df["hladina"] > df["hladina"].quantile(0.9)).astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    df[["srazky","teplota","prietok"]], df["povoden"],
    test_size=0.2, random_state=42
)

lr = LogisticRegression(max_iter=500)
lr.fit(X_train, y_train)
print(classification_report(y_test, lr.predict(X_test)))
print(f"AUC-ROC: {roc_auc_score(y_test, lr.predict_proba(X_test)[:,1]):.3f}")

# ROC křivka
RocCurveDisplay.from_estimator(lr, X_test, y_test)
plt.title("ROC křivka – povodeň")
plt.show()
```

---

## 6. Předpoklady regresních modelů & nápravné kroky

### Přehled předpokladů (Gauss-Markovovy podmínky)

| # | Předpoklad | Jak testovat | Nápravný krok |
|---|------------|-------------|---------------|
| 1 | **Linearita** | Scatter Y vs Ŷ, RESET test | Polynomická regrese, transformace |
| 2 | **Normalita residuí** | Q-Q plot, Shapiro-Wilk, Jarque-Bera | log(Y), Box-Cox transformace |
| 3 | **Homoskedasticita** (stálý rozptyl) | Residuály vs Ŷ, Breusch-Pagan test | log(Y), WLS (vážená regrese) |
| 4 | **Nezávislost residuí** | ACF reziduí, Durbin-Watson | Přidat ARMA členy, diferenciace |
| 5 | **Nulová multikolinearita** | VIF | Odstranit/sloučit korelované prediktory |
| 6 | **Žádné influential outliers** | Cook's distance, leverage | Robustní regrese |

```python
# Kompletní diagnostika reziduí
residuals = model_multi.resid
fitted    = model_multi.fittedvalues

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# 1) Residuály vs Fitted (linearita + homoskedasticita)
axes[0,0].scatter(fitted, residuals, alpha=0.4)
axes[0,0].axhline(0, color="red", linestyle="--")
axes[0,0].set(xlabel="Fitted values", ylabel="Residuals",
              title="Residuals vs Fitted")

# 2) Q-Q plot (normalita)
sm.qqplot(residuals, line="s", ax=axes[0,1])
axes[0,1].set_title("Q-Q plot reziduí")

# 3) Scale-Location (homoskedasticita)
axes[1,0].scatter(fitted, np.sqrt(np.abs(residuals)), alpha=0.4)
axes[1,0].set(xlabel="Fitted", ylabel="√|Residuals|", title="Scale-Location")

# 4) ACF reziduí (nezávislost)
sm.graphics.tsa.plot_acf(residuals, lags=30, ax=axes[1,1])
axes[1,1].set_title("ACF reziduí")

plt.tight_layout(); plt.show()

# Testy
from scipy.stats import shapiro
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import het_breuschpagan

stat, p = shapiro(residuals)
print(f"Shapiro-Wilk: W={stat:.4f}, p={p:.4f}")
# p < 0.05 → residuály nejsou normální

dw = durbin_watson(residuals)
print(f"Durbin-Watson: {dw:.4f}")
# ~2 = žádná autokorelace, <1.5 nebo >2.5 = problém

lm, lm_p, fstat, f_p = het_breuschpagan(residuals, model_multi.model.exog)
print(f"Breusch-Pagan: LM={lm:.4f}, p={lm_p:.4f}")
# p < 0.05 → heteroskedasticita
```

### Box-Cox transformace
```python
from scipy.stats import boxcox

y_transformed, lambda_opt = boxcox(df["hladina"])
print(f"Optimální λ = {lambda_opt:.3f}")
# λ ≈ 0  → log transformace
# λ ≈ 0.5 → √ transformace
# λ ≈ 1  → žádná transformace potřeba
```

---

## 7. Dekompozice časových řad

### Aditivní vs multiplikativní model
```
Aditivní:        Y_t = T_t + S_t + R_t
Multiplikativní: Y_t = T_t · S_t · R_t

kde:
  T_t ... trend (dlouhodobý vývoj)
  S_t ... sezonalita (pravidelné opakující se vzory)
  R_t ... reziduální složka (náhoda)

→ Aditivní: amplituda sezóny je konstantní v čase
→ Multiplikativní: amplituda sezóny roste s úrovní řady
```

```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

# Časová řada musí mít DatetimeIndex
df.index = pd.to_datetime(df["datum"])
ts = df["hladina"].asfreq("D")    # denní frekvence

# Dekompozice
decomp = seasonal_decompose(ts, model="additive", period=365)
decomp.plot()
plt.tight_layout(); plt.show()

# Složky zvlášť
trend    = decomp.trend
seasonal = decomp.seasonal
resid    = decomp.resid
```

### Stacionarita a ADF test
```
Stacionární řada: konstantní střední hodnota, rozptyl a autokovariance v čase
→ Podmínka pro ARMA modely!

ADF test (Augmented Dickey-Fuller):
  H₀: řada má jednotkový kořen (není stacionární)
  H₁: řada je stacionární

Pokud p > 0.05 → diferenciace: ΔY_t = Y_t - Y_{t-1}
```

```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(ts.dropna())
print(f"ADF statistika: {result[0]:.4f}")
print(f"p-hodnota:      {result[1]:.4f}")
print(f"Kritické hodnoty: {result[4]}")
# p > 0.05 → nestacionární → nutno diferencovat

# Diferenciace
ts_diff = ts.diff().dropna()
result2 = adfuller(ts_diff)
print(f"Po diferenciaci p = {result2[1]:.4f}")
```

### ACF a PACF
```
ACF (Autocorrelation Function):
  ρ(k) = Cov(Y_t, Y_{t-k}) / Var(Y_t)
  → korelace řady s jejím posunutím o k kroků
  → pomáhá identifikovat řád q (MA část)

PACF (Partial ACF):
  → korelace Y_t a Y_{t-k} po odstranění efektu mezičlánků
  → pomáhá identifikovat řád p (AR část)

Pravidlo:
  ACF má ostré "cutoff" po q → MA(q)
  PACF má ostré "cutoff" po p → AR(p)
```

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
plot_acf(ts_diff.dropna(),  lags=40, ax=axes[0], title="ACF")
plot_pacf(ts_diff.dropna(), lags=40, ax=axes[1], title="PACF")
plt.tight_layout(); plt.show()
```

---

## 8. Box-Jenkinsova metodologie: ARMA, ARIMA, SARIMA

### ARMA(p, q) – pro stacionární řady
```
AR(p) – autoregresní část:
  Y_t = c + φ₁Y_{t-1} + φ₂Y_{t-2} + ... + φₚY_{t-p} + ε_t
  → Y závisí na p předchozích hodnotách

MA(q) – klouzavý průměr:
  Y_t = μ + ε_t + θ₁ε_{t-1} + ... + θ_qε_{t-q}
  → Y závisí na q předchozích chybách

ARMA(p,q):
  Y_t = c + Σᵢ φᵢY_{t-i} + ε_t + Σⱼ θⱼε_{t-j}
```

### ARIMA(p, d, q) – pro nestacionární řady
```
d = počet diferenciací potřebných ke stacionaritě
→ ARIMA(1,1,1): řadu nejprve diferencujeme (d=1), pak fitujeme ARMA(1,1)
```

### SARIMA(p,d,q)(P,D,Q)[s] – se sezónností
```
s = perioda sezóny (12 pro měsíční, 365 pro denní, 4 pro kvartální)
(P,D,Q) = sezónní AR, diferenciace, MA řády

Příklad: SARIMA(1,1,1)(1,1,1)[12]
→ nestacionární řada s roční sezónností v měsíčních datech
```

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ARIMA – manuálně zvolené řády
model_arima = ARIMA(ts.dropna(), order=(1, 1, 1))
fit_arima   = model_arima.fit()
print(fit_arima.summary())

# SARIMA – sezónní model (měsíční data, roční sezonalita)
ts_mesic = ts.resample("ME").mean()
model_sarima = SARIMAX(ts_mesic.dropna(),
                        order=(1, 1, 1),
                        seasonal_order=(1, 1, 1, 12))
fit_sarima = model_sarima.fit(disp=False)
print(fit_sarima.summary())

# Automatický výběr řádů (auto_arima)
from pmdarima import auto_arima
model_auto = auto_arima(ts.dropna(), seasonal=True, m=365,
                         information_criterion="aic",
                         stepwise=True, trace=True)
print(model_auto.summary())
```

### Predikce a hodnocení
```python
# Prognóza 30 dní dopředu
forecast = fit_sarima.get_forecast(steps=30)
mean_fc   = forecast.predicted_mean
conf_int  = forecast.conf_int()

plt.plot(ts_mesic, label="Pozorovaná data")
plt.plot(mean_fc, color="red", label="Predikce")
plt.fill_between(conf_int.index,
                 conf_int.iloc[:,0], conf_int.iloc[:,1],
                 alpha=0.3, color="red", label="95% CI")
plt.legend(); plt.title("SARIMA prognóza"); plt.show()

# Diagnostika reziduí modelu
fit_sarima.plot_diagnostics(figsize=(12, 8))
plt.show()

# Informační kritéria
print(f"AIC: {fit_sarima.aic:.2f}")
print(f"BIC: {fit_sarima.bic:.2f}")
```

### Identifikační pravidla pro řády
| Co vidíme v ACF/PACF | Model |
|---------------------|-------|
| ACF klesá exponenciálně, PACF utne po p | AR(p) |
| PACF klesá exponenciálně, ACF utne po q | MA(q) |
| Obě klesají postupně | ARMA(p,q) |
| ACF neklesá (hodnoty mimo interval) | nestacionární → diferenciuj |
| ACF/PACF má špičky na násobcích s | sezónní složka → SARIMA |

---

## 9. Dynamické lineární modely (VAR, CCF)

### Křížová korelační funkce (CCF)
```
CCF(k) = Cor(X_t, Y_{t+k})
→ měří, zda X předchází Y o k kroků (nebo naopak)
→ použití: zjistit, zda srážky předcházejí vzestupu hladiny
```

```python
from statsmodels.tsa.stattools import ccf

# CCF: vliv srážek na hladinu (lag 0 až 30 dní)
ccf_values = ccf(df["srazky"], df["hladina"], nlags=30, adjusted=False)

plt.figure(figsize=(10,4))
plt.bar(range(len(ccf_values)), ccf_values)
plt.axhline(1.96/np.sqrt(len(df)), linestyle="--", color="red")
plt.axhline(-1.96/np.sqrt(len(df)), linestyle="--", color="red")
plt.xlabel("Lag (dny)"); plt.ylabel("CCF")
plt.title("Křížová korelace: srážky → hladina")
plt.show()
# Špička na lag=3 → srážky ovlivňují hladinu s 3denním zpožděním
```

### ARIMAX (ARIMA s exogenními proměnnými)
```
Y_t = ARIMA(p,d,q) + β₁X₁_t + β₂X₂_t + ...
→ kombinuje time series model s regresními prediktory
```

```python
model_arimax = SARIMAX(df["hladina"],
                        exog=df[["srazky","teplota"]],
                        order=(1, 1, 1))
fit_arimax = model_arimax.fit(disp=False)
print(fit_arimax.summary())
# Koeficienty exogenních proměnných interpretujeme jako v OLS
```

### VAR (Vector Autoregression) – vzájemná závislost řad
```
[Y_t]   [c₁]   [φ₁₁ φ₁₂] [Y_{t-1}]   [ε₁_t]
[X_t] = [c₂] + [φ₂₁ φ₂₂]·[X_{t-1}] + [ε₂_t]

→ Každá řada závisí na svých i cizích zpožděných hodnotách
→ Granger causality test: testuje, zda X Grangerly způsobuje Y
```

```python
from statsmodels.tsa.vector_ar.var_model import VAR

# Obě řady musí být stacionární!
data_var = pd.DataFrame({
    "hladina": ts_diff.dropna(),
    "srazky":  df["srazky"].diff().dropna()
}).dropna()

model_var = VAR(data_var)
# Výběr řádu podle AIC
results_aic = model_var.select_order(maxlags=10)
print(results_aic.summary())

# Fit s optimálním řádem
p_opt = results_aic.aic
fit_var = model_var.fit(p_opt)
print(fit_var.summary())

# Granger causality test
from statsmodels.tsa.stattools import grangercausalitytests
gc = grangercausalitytests(data_var[["hladina","srazky"]], maxlag=5)
# p < 0.05 → srážky Grangerly způsobují hladinu
```

---

## 10. Postup pro ukázkovou úlohu

### Rozhodovací strom na začátku
```
1. Jsou data časová řada (seřazená v čase, pravidelný interval)?
   ANO → přejdi na analýzu ČŘ
   NE  → nezávislá pozorování → klasická regrese

2. Je závislá proměnná:
   - Spojitá (výška hladiny)?  → lineární / polynomická regrese, ARIMA
   - Binární (povodeň/ne)?     → logistická regrese
   - Kategorická (více tříd)?  → multinomiální logistická regrese

3. Jsou residuály:
   - Neautokorelovane? (DW ≈ 2)  → OLS je OK
   - Autokorelované?             → ARIMA / ARIMAX
   - Heteroskedastické?          → log transformace, WLS
   - Nenormální?                 → Box-Cox transformace
```

### Šablona reportu (Python/R notebook)
```
## 1. Načtení a popis dat
   - head(), describe(), info()
   - Missing values, outliers

## 2. Vizualizace
   - Plot časové řady Y_t
   - Scatter plots Y vs každý prediktor
   - Korelační matice (heatmap)
   - ACF/PACF pokud je to ČŘ

## 3. Příprava dat
   - ADF test stacionarity
   - Diferenciace pokud nestacionární
   - Dekompozice (trend + sezóna)

## 4. Modely (porovnej alespoň 3)
   - Model 1: Jednoduchá regrese (baseline)
   - Model 2: Mnohonásobná regrese (všechny prediktory)
   - Model 3: Kroková regrese (výběr proměnných)
   - Model 4: SARIMA nebo ARIMAX
   - Pro každý: AIC/BIC, R², RMSE, diagnostika reziduí

## 5. Výběr optimálního modelu
   - Porovnání AIC/BIC
   - Interpretace koeficientů
   - Kvalita predikcí (train/test split nebo cross-validation)

## 6. Závěr
   - Který model je nejlepší a proč
   - Jaké faktory nejvíce ovlivňují hladinu
   - Omezení modelu, co by šlo zlepšit
```

### Rychlé porovnání modelů
```python
vysledky = []
for nazev, model in [("OLS simple", model), ("OLS multi", model_multi),
                      ("SARIMA", fit_sarima)]:
    try:
        vysledky.append({
            "model": nazev,
            "AIC":   round(model.aic, 2),
            "BIC":   round(model.bic, 2),
            "R2":    round(getattr(model, "rsquared", float("nan")), 4)
        })
    except: pass

df_vysledky = pd.DataFrame(vysledky).sort_values("AIC")
print(df_vysledky.to_string(index=False))
```
```
model        AIC      BIC       R2
OLS multi   1842.3   1865.1   0.7821
OLS simple  2103.5   2118.2   0.5943
SARIMA      1798.6   1823.4      NaN   ← nejlepší AIC
```

---

*Aktualizováno pro státnici – Python (statsmodels, scipy, sklearn, pmdarima)*