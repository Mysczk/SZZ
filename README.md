# Rozcestník – cheat-sheety

Každý soubor pokrývá jedno téma. Otevři příslušný podle zadání úlohy.

---

## Témata

### I. Relační databáze a OLAP
📄 [`db_olap/README.md`](db_olap/README.md)

PostgreSQL · SQLAlchemy · pandas · Matplotlib

- Logický návrh, normalizace, E-R diagram
- CREATE TABLE, domény, omezení, FK
- SELECT, JOIN, WHERE, GROUP BY, ORDER BY
- Transakce, analytické (window) funkce
- Uložené procedury, triggery, rekurzivní CTE
- Kurzory, ORM (SQLAlchemy)
- OLAP – ROLAP/MOLAP/HOLAP, Star/Snowflake schema, DW vs DM

---

### II. NoSQL databáze
📄 [`NoSQL/README.md`](NoSQL/README.md)

MongoDB · pymongo · pandas · Matplotlib

- SQL vs NoSQL – kdy co zvolit, zdůvodnění
- Dokumentový model, embedding vs referencing
- Připojení, insert_one / insert_many
- Základní dotazy – find, operátory, dot-notation
- Agregační pipeline – $match, $group, $unwind, $lookup, $addFields
- JSONB v PostgreSQL (bonus)

---

### III. Pokročilé statistické metody a časové řady
📄 [`psm_cas/README.md`](psm_cas/README.md)

Python · statsmodels · scipy · sklearn · pmdarima

- Lineární a mnohonásobná regrese (OLS, R², AIC/BIC, VIF)
- Nelineární modely, polynomická regrese, Box-Cox
- ANOVA, logistická regrese, odds ratio
- Předpoklady regresních modelů + nápravné kroky
- Dekompozice časových řad, stacionarita, ADF test, ACF/PACF
- ARMA, ARIMA, SARIMA – matematika + kód
- CCF, ARIMAX, VAR, Grangerova kauzalita

---

### IV. Úvod do strojového učení
📄 [`usu/README.md`](usu/README.md)

Python · scikit-learn · Keras/TensorFlow · pandas

- Příprava dat – NaN, outliers, one-hot encoding, škálování
- PCA vs LDA – kdy co použít
- Metriky – accuracy, F1, AUC-ROC, MAE, RMSE, R²
- Rozhodovací stromy, Random Forest, SVR/SVC, logistická regrese
- Pipeline, GridSearchCV, RandomizedSearchCV, cross-validace
- MLP – matematika, Keras implementace, EarlyStopping, Keras Tuner
- CNN – základní princip

---

### V. Počítačové zpracování signálu
📄 [`pzs/README.md`](pzs/README.md)

Python · NumPy · SciPy · wfdb · Matplotlib

- Základní charakteristiky signálu – amplituda, frekvence, fáze, RMS
- Konvoluce, korelace, kovariance
- FFT – DFT vzorec, rfft, magnitudové spektrum, spektrogram
- Filtrace – Butterworth BP/HP/LP/notch, filtfilt, frekvenční charakteristika
- Hilbertova transformace, průměrování, matchovaný filtr
- Načtení EKG (wfdb, MIT-BIH databáze)
- Pan-Tompkins detektor R-vrcholů
- Výpočet tepové frekvence, evaluace (Se, F1)

---

### VI. OOP návrhové vzory (C#)
📄 [`oonv/README.md`](oonv/README.md)

C# · .NET 8 · xUnit · PlantUML

- Typový systém, specifikátory přístupu
- Polymorfismus – rozhraní vs dědičnost
- **Vytvářející:** Singleton, Factory Method, Prototype
- **Strukturální:** Adapter, Decorator, Bridge, Flyweight
- **Chování:** Command, Observer, Iterator, Memento, Strategy
- UML notace, PlantUML příklady
- xUnit testy – [Fact], [Theory], [InlineData]

---

### VII. Vývoj mobilní aplikace
📄 [`mobil/README.md`](mobil/README.md)

React Native · Expo · iOS · expo-sqlite · expo-location

- Setup projektu, struktura složek
- Základní komponenty (iOS ekvivalenty)
- Navigace – expo-router, dvě obrazovky, předávání parametrů
- RSS/XML parsování, JSON fetch
- SQLite – init, CRUD, filtr posledních N dní
- Senzory, GPS – oprávnění, cleanup subscriptions
- Background fetch – ⚠️ nefunguje v Expo Go na iOS
- iOS specifika – Info.plist, HTTPS povinné, oprávnění
- UML diagramy aktivit a tříd

---

### VIII. Vývoj webové aplikace
📄 [`web/README.md`](web/README.md)

PHP 8 · MySQL · SimpleXML · DOMDocument · Bootstrap 5

- XML – struktura, well-formed pravidla, XSD validace
- SimpleXML a DOMDocument – čtení, XPath, zápis, smazání
- PHP syntaxe, funkce, OOP (PHP 8)
- Sessions, cookies, přihlášení, password_hash
- PDO – připojení, CRUD prepared statements, schéma DB
- Bezpečnost – SQL injection, XSS, CSRF, hashování
- REST API – GET/POST/PUT/DELETE endpoint + fetch z JS

---

## Rychlá orientace podle technologie

| Technologie | Složka |
|-------------|--------|
| PostgreSQL / SQL | `db_olap` |
| MongoDB | `NoSQL` |
| Python / pandas | `db_olap`, `NoSQL`, `psm_cas`, `usu`, `pzs` |
| scikit-learn | `usu` |
| Keras / TensorFlow | `usu` |
| statsmodels / scipy | `psm_cas` |
| NumPy / SciPy | `pzs` |
| C# / .NET | `oonv` |
| React Native / Expo | `mobil` |
| PHP / MySQL | `web` |
| XML / XSD | `web` |