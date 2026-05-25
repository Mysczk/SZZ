# V. Počítačové zpracování signálu

> Cheat-sheet pro praktickou státnici. EKG signály, Fourierova transformace, filtrace, detekce R-vrcholů.

---

## Obsah
1. [Základní charakteristiky signálu](#1-základní-charakteristiky-signálu)
2. [NumPy – základní práce se signálem](#2-numpy--základní-práce-se-signálem)
3. [Metody časové oblasti – konvoluce, korelace, kovariance](#3-metody-časové-oblasti--konvoluce-korelace-kovariance)
4. [Fourierova transformace – frekvenční oblast](#4-fourierova-transformace--frekvenční-oblast)
5. [Filtrace šumu](#5-filtrace-šumu)
6. [Posílení signálu v časové oblasti](#6-posílení-signálu-v-časové-oblasti)
7. [Načtení EKG dat (wfdb)](#7-načtení-ekg-dat-wfdb)
8. [Detekce R-vrcholů a výpočet tepové frekvence](#8-detekce-r-vrcholů-a-výpočet-tepové-frekvence)
9. [Ukázková úloha – kompletní pipeline](#9-ukázková-úloha--kompletní-pipeline)

---

## 1. Základní charakteristiky signálu

### Matematická definice
```
Harmonický signál:
  x(t) = A · sin(2π·f·t + φ)

kde:
  A   ... amplituda [jednotka signálu, např. mV]
  f   ... frekvence [Hz] = počet period za sekundu
  T   ... perioda [s] = 1/f
  φ   ... fáze [rad] = počáteční posun v čase
  ω   ... úhlová frekvence [rad/s] = 2π·f

Vzorkovací teorém (Nyquist-Shannon):
  f_vzork ≥ 2 · f_max
  → aby šlo rekonstruovat signál, musíme vzorkovat alespoň 2× rychleji
    než je nejvyšší frekvence v signálu
  → EKG typicky 250–500 Hz (QRS komplex sahá do ~40 Hz)
```

### Výpočet základních vlastností
```python
import numpy as np
import matplotlib.pyplot as plt

# Vytvoření syntetického signálu pro demonstraci
fs = 500          # vzorkovací frekvence [Hz]
T_signal = 5      # délka signálu [s]
t = np.arange(0, T_signal, 1/fs)   # časová osa

# Složený signál: 5 Hz + 20 Hz + šum
x = (1.5 * np.sin(2*np.pi*5*t) +
     0.5 * np.sin(2*np.pi*20*t + np.pi/4) +
     0.2 * np.random.randn(len(t)))

# --- Základní vlastnosti ---
amplituda    = (x.max() - x.min()) / 2        # polovina peak-to-peak
offset       = x.mean()                        # stejnosměrná složka (DC)
vykon        = np.mean(x**2)                   # průměrný výkon signálu
energie      = np.sum(x**2) / fs               # energie [J ~ V²·s]
rms          = np.sqrt(vykon)                  # RMS (Root Mean Square)
rozptyl      = np.var(x)                       # rozptyl

print(f"Amplituda:  {amplituda:.4f}")
print(f"DC offset:  {offset:.4f}")
print(f"RMS:        {rms:.4f}")
print(f"Výkon:      {vykon:.4f}")
print(f"Energie:    {energie:.4f}")
print(f"Rozptyl:    {rozptyl:.4f}")
```
```
Amplituda:  1.5823
DC offset:  0.0031
RMS:        1.1247
Výkon:      1.2650
Energie:    6.3250
Rozptyl:    1.2649
```

### Perioda z nulových průchodů
```python
# Nulové průchody (zero crossings) → odhad periody
zero_crossings = np.where(np.diff(np.sign(x)))[0]
periods = np.diff(zero_crossings) / fs * 2   # ×2 protože půlperioda
T_odhad = np.median(periods)
f_odhad = 1 / T_odhad
print(f"Odhadnutá perioda: {T_odhad:.4f} s, frekvence: {f_odhad:.2f} Hz")
```

### Trend signálu
```python
# Lineární trend (polynomická regrese stupně 1)
koef = np.polyfit(t, x, deg=1)   # [slope, intercept]
trend = np.polyval(koef, t)
x_detrended = x - trend

print(f"Trend: slope={koef[0]:.4f} [jednotka/s], intercept={koef[1]:.4f}")

plt.figure(figsize=(12,4))
plt.plot(t, x, alpha=0.7, label="Originál")
plt.plot(t, trend, color="red", lw=2, label=f"Trend (slope={koef[0]:.3f})")
plt.plot(t, x_detrended, alpha=0.7, label="Detrendovaný")
plt.legend(); plt.xlabel("Čas [s]"); plt.title("Detrendování signálu")
plt.tight_layout(); plt.show()
```

---

## 2. NumPy – základní práce se signálem

```python
import numpy as np

# Vytvoření signálu
fs = 1000                                    # Hz
t  = np.linspace(0, 1, fs, endpoint=False)  # 1 sekunda

# Vektorové operace (bez smyček!)
x  = np.sin(2*np.pi*50*t)          # 50 Hz sinusoida
x2 = 0.5 * np.cos(2*np.pi*120*t)   # 120 Hz kosinusoida
x_sum = x + x2 + 0.1*np.random.randn(fs)

# Indexování a slicing
segment = x_sum[100:200]            # vzorky 100–199
okno    = x_sum[fs//2:]             # druhá polovina signálu

# Statistiky po oknech (numpy stride tricks)
okno_delka = 100  # vzorků
n_oken = len(x_sum) // okno_delka
x_reshaped = x_sum[:n_oken*okno_delka].reshape(n_oken, okno_delka)
rms_okna = np.sqrt(np.mean(x_reshaped**2, axis=1))  # RMS každého okna

# Normalizace
x_norm_01  = (x_sum - x_sum.min()) / (x_sum.max() - x_sum.min())  # [0,1]
x_norm_std = (x_sum - x_sum.mean()) / x_sum.std()                  # z-score

# Padding a ořez
x_padded   = np.pad(x_sum, (50, 50), mode="constant", constant_values=0)
x_zeropad  = np.pad(x_sum, (0, 1024-len(x_sum)), mode="constant")  # pro FFT
```

---

## 3. Metody časové oblasti – konvoluce, korelace, kovariance

### Konvoluce
```
Matematicky:
  (x ∗ h)[n] = Σₖ x[k] · h[n-k]

Interpretace:
  → aplikace filtru h (impulzní odezva) na signál x
  → klouzavý průměr = konvoluce s obdélníkovým oknem
  → výsledná délka = len(x) + len(h) - 1

Použití v DSP:
  → vyhlazování (low-pass filtr)
  → detekce hran (derivační filtr)
  → matchovaný filtr (detekce vzoru)
```

```python
# Klouzavý průměr přes konvoluci
okno_sirka = 25                              # vzorků (~50 ms při 500 Hz)
h_prumer   = np.ones(okno_sirka) / okno_sirka
x_smooth   = np.convolve(x_sum, h_prumer, mode="same")
# mode="same" → výstup má stejnou délku jako vstup

# Gaussovské vyhlazení (lepší než obdélník – méně "překmitu")
from scipy.ndimage import gaussian_filter1d
x_gauss = gaussian_filter1d(x_sum, sigma=5)

plt.figure(figsize=(12, 4))
plt.plot(t, x_sum, alpha=0.4, label="Originál + šum")
plt.plot(t, x_smooth, lw=2, label=f"Klouzavý průměr (w={okno_sirka})")
plt.plot(t, x_gauss,  lw=2, label="Gaussovské vyhlazení (σ=5)")
plt.legend(); plt.xlabel("Čas [s]"); plt.title("Konvoluce – vyhlazení")
plt.tight_layout(); plt.show()
```

### Korelace a kovariance
```
Autokorelace:
  R_xx[k] = Σₙ x[n] · x[n+k]
  → měří podobnost signálu se sebou samým posunutým o k vzorků
  → maximum při k=0, periodické vrcholy při k=T → odhalí periodu

Křížová korelace:
  R_xy[k] = Σₙ x[n] · y[n+k]
  → měří podobnost dvou různých signálů
  → peak při lag=k₀ → signál y předchází/zaostává za x o k₀ vzorků

Normalizovaná (Pearsonova) korelace: hodnoty v [-1, 1]
```

```python
# Autokorelace
autocorr = np.correlate(x_sum, x_sum, mode="full")
autocorr = autocorr[len(x_sum)-1:]           # jen kladné lagy
lags_ac  = np.arange(len(autocorr)) / fs     # převod na sekundy

plt.figure(figsize=(10, 3))
plt.plot(lags_ac[:int(0.2*fs)], autocorr[:int(0.2*fs)])
plt.xlabel("Lag [s]"); plt.ylabel("Autokorelace")
plt.title("Autokorelace – detekce periody"); plt.show()

# Křížová korelace (zpožděný signál)
delay_samples = 50
y_delayed = np.roll(x_sum, delay_samples)
crosscorr = np.correlate(x_sum, y_delayed, mode="full")
lag_peak  = np.argmax(crosscorr) - (len(x_sum)-1)
print(f"Detekované zpoždění: {lag_peak} vzorků = {lag_peak/fs*1000:.1f} ms")

# Numpy kovariance (normalizovaná) – pro více signálů naráz
cov_matrix = np.cov(np.vstack([x_sum, y_delayed]))
corr_coef  = np.corrcoef(x_sum, y_delayed)
print(f"Korelační koef.: {corr_coef[0,1]:.4f}")
```

---

## 4. Fourierova transformace – frekvenční oblast

### Matematická definice
```
DFT (Discrete Fourier Transform):
  X[k] = Σₙ x[n] · e^(-j·2π·k·n/N)    pro k = 0, 1, ..., N-1

  X[k] ... komplexní koeficient k-té frekvenční složky
  |X[k]| ... amplituda (magnitudové spektrum)
  ∠X[k]  ... fáze (fázové spektrum)
  f_k = k · f_vzork / N    ... frekvence k-té složky [Hz]

FFT = rychlý algoritmus pro DFT (O(N log N) místo O(N²))

Parsovalův teorém:
  Σ|x[n]|² = (1/N) · Σ|X[k]|²
  → energie v časové doméně = energie ve frekvenční doméně

Symetrie reálného signálu:
  X[k] = X*[N-k]  → spektrum symetrické, zobrazujeme jen polovinu [0, f_vzork/2]
  Nyquistova frekvence = f_vzork / 2
```

```python
from scipy.fft import fft, fftfreq, rfft, rfftfreq

N  = len(x_sum)
dt = 1 / fs

# FFT
X  = fft(x_sum)
f  = fftfreq(N, d=dt)        # frekvenční osa

# Pro reálný signál stačí rfft (pouze kladné frekvence)
X_r = rfft(x_sum)
f_r = rfftfreq(N, d=dt)

amplitudy  = (2/N) * np.abs(X_r)   # ×2 kvůli symetrii (jen pol. spektra)
amplitudy[0] /= 2                   # DC složka se nezdvojuje

# Výkonové spektrum (PSD)
psd = amplitudy**2

plt.figure(figsize=(12, 8))

plt.subplot(3,1,1)
plt.plot(t, x_sum, lw=0.8)
plt.xlabel("Čas [s]"); plt.ylabel("Amplituda"); plt.title("Signál v čase")

plt.subplot(3,1,2)
plt.plot(f_r, amplitudy, color="darkorange")
plt.xlabel("Frekvence [Hz]"); plt.ylabel("|X(f)|")
plt.title("Magnitudové spektrum (FFT)")
plt.axvline(50, color="red", linestyle="--", label="50 Hz")
plt.axvline(120, color="green", linestyle="--", label="120 Hz")
plt.legend()

plt.subplot(3,1,3)
plt.semilogy(f_r, psd, color="purple")   # log měřítko pro výkon
plt.xlabel("Frekvence [Hz]"); plt.ylabel("Výkon [dB]")
plt.title("Výkonové spektrum")

plt.tight_layout(); plt.show()

# Dominantní frekvence
idx_max   = np.argmax(amplitudy[1:]) + 1   # přeskočí DC složku
dom_freq  = f_r[idx_max]
print(f"Dominantní frekvence: {dom_freq:.2f} Hz")
```

### Spektrogram (čas-frekvence)
```python
from scipy.signal import spectrogram

f_spec, t_spec, Sxx = spectrogram(x_sum, fs=fs,
                                    nperseg=128,     # délka okna FFT
                                    noverlap=64)     # překryv oken
plt.figure(figsize=(10, 4))
plt.pcolormesh(t_spec, f_spec, 10*np.log10(Sxx), shading="gouraud", cmap="viridis")
plt.colorbar(label="Výkon [dB]")
plt.ylabel("Frekvence [Hz]"); plt.xlabel("Čas [s]")
plt.title("Spektrogram"); plt.show()
```

---

## 5. Filtrace šumu

### Typy filtrů
```
Low-pass  (dolní propust):  propustí <f_cutoff,  potlačí >f_cutoff  → vyhlazení
High-pass (horní propust):  propustí >f_cutoff,  potlačí <f_cutoff  → odstranění DC/trendu
Band-pass (pásmová propust):propustí f_low–f_high                   → EKG: 0.5–40 Hz
Band-stop (pásmová zádrž):  potlačí  f_low–f_high                   → notch filtr 50 Hz (síťový šum)

Butterworth: maximálně plochá propustná oblast (bez zvlnění)
  → nejčastější volba pro biomedicínská data
  → parametry: řád filtru N (strmost), cutoff frekvence
```

```python
from scipy.signal import butter, filtfilt, iirnotch, sosfilt, sosfreqz

def butter_filter(data, cutoff, fs, btype="low", order=4):
    """
    btype: 'low', 'high', 'band', 'bandstop'
    cutoff: číslo (pro low/high) nebo [f_low, f_high] (pro band)
    """
    nyq  = fs / 2
    norm = np.array(cutoff) / nyq           # normalizace na Nyquist
    sos  = butter(order, norm, btype=btype, output="sos")
    return filtfilt(sos, np.ones(1), data)   # filtfilt = nulová fázová odezva!
    # Alternativa: sosfilt(sos, data) – kauzální, zavádí fázové zpoždění

# Low-pass: odstranění vysokofrekvenčního šumu
x_lp = butter_filter(x_sum, cutoff=30, fs=fs, btype="low", order=4)

# High-pass: odstranění driftu baseline
x_hp = butter_filter(x_sum, cutoff=0.5, fs=fs, btype="high", order=2)

# Band-pass: EKG pásmo (typicky 0.5–40 Hz nebo 1–40 Hz)
x_bp = butter_filter(x_sum, cutoff=[0.5, 40], fs=fs, btype="band", order=4)

# Notch filtr: odstranění síťového brumu 50 Hz
b_notch, a_notch = iirnotch(w0=50, Q=30, fs=fs)
x_notch = filtfilt(b_notch, a_notch, x_sum)

# Vizualizace frekvenční charakteristiky filtru
sos_bp = butter(4, [0.5/250, 40/250], btype="band", output="sos")
w, h   = sosfreqz(sos_bp, worN=2000, fs=fs)
plt.figure(figsize=(8,4))
plt.plot(w, 20*np.log10(np.abs(h)))
plt.xlabel("Frekvence [Hz]"); plt.ylabel("Zisk [dB]")
plt.title("Frekvenční charakteristika BP filtru (0.5–40 Hz)")
plt.axhline(-3, color="red", linestyle="--", label="-3 dB")
plt.legend(); plt.grid(); plt.show()
```

### Filtrace ve frekvenční doméně (přímá manipulace spektra)
```python
# Přímé vynulování frekvenčních složek (ideální, ale způsobí Gibbsův jev)
X_filt = rfft(x_sum).copy()
freqs  = rfftfreq(len(x_sum), 1/fs)

# Potlač vše nad 40 Hz
X_filt[freqs > 40] = 0

# Potlač síťový brum 50 Hz ± 2 Hz
brum = (freqs >= 48) & (freqs <= 52)
X_filt[brum] = 0

from scipy.fft import irfft
x_filtered_fft = irfft(X_filt, n=len(x_sum))
```

---

## 6. Posílení signálu v časové oblasti

### Průměrování (signal averaging)
```
Pokud máme opakující se vzor (např. QRS komplex v EKG):
  x̄[n] = (1/M) · Σₘ xₘ[n]

→ SNR (Signal-to-Noise Ratio) se zlepší √M krát
→ SNR_dB = 20·log₁₀(√M) = 10·log₁₀(M) [dB]
→ Pro M=100 průměrů: zisk 20 dB
```

```python
# Průměrování EKG cyklů kolem R-vrcholů
def prumer_cyklu(signal, r_peaks, okno_pred, okno_po):
    """okno_pred, okno_po: počet vzorků před/po R-vrcholu"""
    cykly = []
    for r in r_peaks:
        start = r - okno_pred
        end   = r + okno_po
        if start >= 0 and end < len(signal):
            cykly.append(signal[start:end])
    cykly  = np.array(cykly)
    prumer = np.mean(cykly, axis=0)
    std    = np.std(cykly, axis=0)
    return prumer, std, cykly

# Matchovaný filtr (matched filter) – korelace se vzorovou šablonou
def matched_filter(signal, sablona):
    """Detekuje výskyt šablony v signálu přes křížovou korelaci"""
    sablona_norm = sablona / np.linalg.norm(sablona)  # normalizace
    korelace = np.correlate(signal, sablona_norm, mode="same")
    return korelace
```

### Obálka signálu (Hilbertova transformace)
```python
from scipy.signal import hilbert

# Analytický signál: z(t) = x(t) + j·H{x(t)}
analyticke = hilbert(x_sum)
obalka     = np.abs(analyticke)          # amplitudová obálka
instantni_f = np.diff(np.unwrap(np.angle(analyticke))) / (2*np.pi/fs)

plt.figure(figsize=(10, 4))
plt.plot(t, x_sum, alpha=0.6, label="Signál")
plt.plot(t, obalka, lw=2, color="red", label="Obálka (Hilbert)")
plt.legend(); plt.xlabel("Čas [s]"); plt.title("Amplitudová obálka")
plt.show()
```

---

## 7. Načtení EKG dat (wfdb)

```python
# Instalace: pip install wfdb
import wfdb
import numpy as np

# MIT-BIH Arrhythmia Database (veřejná, 48 záznamů, 360 Hz)
# https://physionet.org/content/mitdb/

# Stažení jednoho záznamu
record = wfdb.rdrecord("mitdb/100", pn_dir="mitdb")
# nebo lokálně: wfdb.rdrecord("100", pb_dir="./data/mitdb/")

signal    = record.p_signal[:, 0]   # první kanál (MLII odvod)
fs        = record.fs               # 360 Hz
n_samples = record.sig_len
t         = np.arange(n_samples) / fs

print(f"Délka záznamu:     {n_samples/fs/60:.1f} minut")
print(f"Vzorkovací freq.:  {fs} Hz")
print(f"Počet kanálů:      {record.n_sig}")
print(f"Kanály:            {record.sig_name}")

# Načtení anotací (zlatý standard R-vrcholů)
ann = wfdb.rdann("mitdb/100", "atr", pn_dir="mitdb")
r_peaks_ref = ann.sample          # pozice R-vrcholů [vzorky]
ann_typy    = ann.symbol          # typy úderů: 'N'=normal, 'V'=VPC, ...

# Zobrazení prvních 10 sekund
plt.figure(figsize=(14, 4))
t_plot = t[t <= 10]
plt.plot(t_plot, signal[:len(t_plot)], lw=0.8, label="EKG (MLII)")
# Vyznač referenční R-vrcholy
r_v_okne = r_peaks_ref[r_peaks_ref < 10*fs]
plt.scatter(r_v_okne/fs, signal[r_v_okne], color="red", s=50,
            zorder=5, label="R-vrcholy (anotace)")
plt.xlabel("Čas [s]"); plt.ylabel("Amplituda [mV]")
plt.title("EKG signál – záznam MIT-BIH 100"); plt.legend()
plt.tight_layout(); plt.show()

# Hromadné stažení celé databáze (seznam záznamů)
zaznamy = wfdb.get_record_list("mitdb")
print(f"Celkem záznamů: {len(zaznamy)}")
```

---

## 8. Detekce R-vrcholů a výpočet tepové frekvence

### Předzpracování EKG
```python
from scipy.signal import butter, filtfilt

def preprocess_ekg(signal, fs):
    """Standardní předzpracování EKG před detekcí R-vrcholů."""
    nyq = fs / 2

    # 1) Band-pass filtr (0.5–40 Hz): odstraní baseline drift i EMG šum
    sos_bp = butter(4, [0.5/nyq, 40/nyq], btype="band", output="sos")
    sig_bp = filtfilt(sos_bp, np.ones(1), signal) if False else \
             __import__("scipy.signal", fromlist=["sosfiltfilt"]).sosfiltfilt(sos_bp, signal)

    # Jednodušeji:
    b, a = butter(4, [0.5/nyq, 40/nyq], btype="band")
    sig_filt = filtfilt(b, a, signal)

    # 2) Detrendování (odstranění pomalého driftu)
    from scipy.signal import detrend
    sig_filt = detrend(sig_filt, type="linear")

    return sig_filt
```

### Pan-Tompkins algoritmus (klasický detektor QRS)
```
Princip Pan-Tompkins (1985):
  1. Band-pass filtr (5–15 Hz) – zvýraznění QRS
  2. Derivace – zdůrazní strmé hrany QRS
  3. Umocnění – vše kladné, zesílí velké hodnoty
  4. Moving window integration – vyhlazení, detekce obálky
  5. Prahování s adaptivním prahem – detekce vrcholů

Výsledek: robustní detekce R-vrcholů i při šumu
```

```python
from scipy.signal import find_peaks

def pan_tompkins(signal, fs):
    """
    Zjednodušená implementace Pan-Tompkins detektoru R-vrcholů.
    Vrací indexy detekovaných R-vrcholů.
    """
    nyq = fs / 2

    # Krok 1: Band-pass (5–15 Hz pro QRS komplex)
    b, a = butter(1, [5/nyq, 15/nyq], btype="band")
    sig_bp = filtfilt(b, a, signal)

    # Krok 2: Derivace (zdůrazní rychlé změny = QRS strmé hrany)
    sig_diff = np.diff(sig_bp, prepend=sig_bp[0])

    # Krok 3: Umocnění (vše kladné, amplifikace vrcholů)
    sig_sq = sig_diff ** 2

    # Krok 4: Moving window integration (~150 ms okno)
    w = int(0.15 * fs)
    sig_int = np.convolve(sig_sq, np.ones(w)/w, mode="same")

    # Krok 5: Detekce vrcholů s minimální vzdáleností 200 ms (max ~300 BPM)
    min_dist = int(0.2 * fs)
    prah     = 0.3 * sig_int.max()    # adaptivní práh: 30 % maxima
    peaks, props = find_peaks(sig_int, height=prah, distance=min_dist)

    # Zpřesnění: najdi skutečné maximum EKG v okolí ±50 ms každého vrcholu
    okno_zpres = int(0.05 * fs)
    r_peaks = []
    for p in peaks:
        start = max(0, p - okno_zpres)
        end   = min(len(signal), p + okno_zpres)
        r_peaks.append(start + np.argmax(signal[start:end]))

    return np.array(r_peaks), sig_int

# --- Alternativa: scipy.signal.find_peaks přímo na filtrovaném signálu ---
def detektor_jednoduchý(signal, fs):
    b, a = butter(4, [1/nyq, 40/nyq], btype="band") if False else \
           butter(4, [1/(fs/2), 40/(fs/2)], btype="band")
    sig_f = filtfilt(b, a, signal)
    prah  = np.mean(sig_f) + 1.5 * np.std(sig_f)
    peaks, _ = find_peaks(sig_f, height=prah, distance=int(0.2*fs))
    return peaks
```

### Výpočet tepové frekvence
```python
def vypocet_tf(r_peaks, fs, metoda="klouzavy"):
    """
    r_peaks: indexy R-vrcholů [vzorky]
    fs:      vzorkovací frekvence [Hz]
    metoda:  'okamzita' nebo 'klouzavy'

    Vrací: časy [s] a tepová frekvence [BPM]
    """
    # RR intervaly [sekundy]
    rr_intervaly = np.diff(r_peaks) / fs

    # Okamžitá TF pro každý RR interval
    tf_okamzita = 60 / rr_intervaly           # [BPM]
    t_tf        = r_peaks[1:] / fs            # čas = pozice druhého R-vrcholu

    if metoda == "klouzavy":
        # Klouzavý průměr přes 5 RR intervalů (vyhlazení)
        k   = 5
        tf  = np.convolve(tf_okamzita, np.ones(k)/k, mode="same")
        return t_tf, tf
    else:
        return t_tf, tf_okamzita

# Vizualizace s průběhem signálu
def plot_tf(signal, fs, r_peaks, t_tf, tf):
    t = np.arange(len(signal)) / fs
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # Panel 1: EKG s detekovanými R-vrcholy
    axes[0].plot(t, signal, lw=0.7, color="steelblue", label="EKG")
    axes[0].scatter(r_peaks/fs, signal[r_peaks], color="red",
                    s=60, zorder=5, label="R-vrcholy")
    axes[0].set_ylabel("Amplituda [mV]")
    axes[0].set_title("EKG signál s detekovanými R-vrcholy")
    axes[0].legend(loc="upper right")

    # Panel 2: Tepová frekvence v čase
    axes[1].plot(t_tf, tf, color="darkorange", lw=1.5)
    axes[1].set_xlabel("Čas [s]")
    axes[1].set_ylabel("Tepová frekvence [BPM]")
    axes[1].set_title(f"Tepová frekvence – průměr: {tf.mean():.1f} BPM")
    axes[1].set_ylim(30, 200)
    axes[1].axhline(tf.mean(), color="red", linestyle="--",
                    alpha=0.6, label=f"Průměr: {tf.mean():.1f} BPM")
    axes[1].legend()

    plt.tight_layout(); plt.show()
```

### Hodnocení kvality detektoru
```python
def evaluate_detektor(r_peaks_det, r_peaks_ref, fs, tolerance_ms=50):
    """
    Porovnání detekovaných R-vrcholů s referenčními anotacemi.

    Metriky:
      Sensitivity (Se) = TP / (TP + FN)  ... kolik R jsme detekovali
      Positive Predictivity (P+) = TP / (TP + FP)  ... kolik detekcí je správných
      F1 = 2·Se·P+ / (Se+P+)
    """
    tol = int(tolerance_ms / 1000 * fs)   # tolerance v vzorcích
    TP, FP, FN = 0, 0, 0
    pouzite_ref = set()

    for det in r_peaks_det:
        # Hledej nejbližší referenční vrchol v toleranci
        vzdalenosti = np.abs(r_peaks_ref - det)
        idx_min     = np.argmin(vzdalenosti)
        if vzdalenosti[idx_min] <= tol and idx_min not in pouzite_ref:
            TP += 1
            pouzite_ref.add(idx_min)
        else:
            FP += 1

    FN = len(r_peaks_ref) - TP

    Se  = TP / (TP + FN) if (TP + FN) > 0 else 0
    Pp  = TP / (TP + FP) if (TP + FP) > 0 else 0
    F1  = 2*Se*Pp / (Se+Pp) if (Se+Pp) > 0 else 0

    print(f"TP={TP}, FP={FP}, FN={FN}")
    print(f"Sensitivity (Se): {Se:.4f} ({Se*100:.2f} %)")
    print(f"Positive Pred.  : {Pp:.4f} ({Pp*100:.2f} %)")
    print(f"F1-skóre:         {F1:.4f}")
    return {"Se": Se, "Pp": Pp, "F1": F1}
```

---

## 9. Ukázková úloha – kompletní pipeline

```python
import wfdb
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks, detrend

# ──────────────────────────────────────────────
# KROK 1: Načtení dat
# ──────────────────────────────────────────────
zaznamy = ["100", "101", "102", "103", "104"]   # subset databáze

def nacti_zaznam(rec_id):
    rec = wfdb.rdrecord(rec_id, pn_dir="mitdb")
    ann = wfdb.rdann(rec_id, "atr", pn_dir="mitdb")
    signal = rec.p_signal[:, 0]
    fs     = rec.fs
    return signal, fs, ann.sample

# ──────────────────────────────────────────────
# KROK 2: Předzpracování
# ──────────────────────────────────────────────
def preprocess(signal, fs):
    # Detrendování – lineární drift
    sig = detrend(signal, type="linear")
    # Band-pass 0.5–40 Hz
    b, a = butter(4, [0.5/(fs/2), 40/(fs/2)], btype="band")
    sig  = filtfilt(b, a, sig)
    return sig

# ──────────────────────────────────────────────
# KROK 3: Detekce R-vrcholů (Pan-Tompkins)
# ──────────────────────────────────────────────
def detekuj_r_vrcholy(signal, fs):
    nyq = fs / 2
    # BP pro QRS
    b, a   = butter(1, [5/nyq, 15/nyq], btype="band")
    sig_bp = filtfilt(b, a, signal)
    # Derivace + umocnění + integrace
    sig_d  = np.diff(sig_bp, prepend=sig_bp[0])
    sig_sq = sig_d**2
    w      = int(0.15 * fs)
    sig_i  = np.convolve(sig_sq, np.ones(w)/w, mode="same")
    # Detekce vrcholů
    prah   = 0.3 * sig_i.max()
    peaks, _ = find_peaks(sig_i, height=prah, distance=int(0.2*fs))
    # Zpřesnění na původní signál
    hwin   = int(0.05 * fs)
    r_peaks = [p - hwin + np.argmax(signal[max(0,p-hwin):p+hwin])
               for p in peaks]
    return np.array(r_peaks)

# ──────────────────────────────────────────────
# KROK 4: Výpočet TF + Graf pro jeden záznam
# ──────────────────────────────────────────────
signal_raw, fs, r_ref = nacti_zaznam("100")
signal_filt = preprocess(signal_raw, fs)
r_peaks     = detekuj_r_vrcholy(signal_filt, fs)
t           = np.arange(len(signal_raw)) / fs

# Okamžitá TF
rr  = np.diff(r_peaks) / fs
tf  = 60 / rr
t_tf = r_peaks[1:] / fs
# Klouzavý průměr
tf_smooth = np.convolve(tf, np.ones(5)/5, mode="same")

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# Syrový signál
axes[0].plot(t[:10*fs], signal_raw[:10*fs], lw=0.6, color="gray")
axes[0].set_title("EKG – surový signál"); axes[0].set_ylabel("mV")

# Filtrovaný + R-vrcholy
axes[1].plot(t[:10*fs], signal_filt[:10*fs], lw=0.7, color="steelblue")
r_okno = r_peaks[r_peaks < 10*fs]
axes[1].scatter(r_okno/fs, signal_filt[r_okno], color="red", s=50, zorder=5)
axes[1].set_title("EKG – filtrovaný + R-vrcholy"); axes[1].set_ylabel("mV")

# Tepová frekvence
axes[2].plot(t_tf[t_tf <= 10*fs/fs], tf_smooth[t_tf <= 10*fs/fs],
             color="darkorange", lw=1.5)
axes[2].set_title(f"Tepová frekvence (průměr: {tf.mean():.1f} BPM)")
axes[2].set_ylabel("BPM"); axes[2].set_xlabel("Čas [s]")

plt.tight_layout(); plt.savefig("tf_signal.png", dpi=150); plt.show()

# ──────────────────────────────────────────────
# KROK 5: Přehledový graf pro celou databázi
# ──────────────────────────────────────────────
db_results = []
for zaz_id in zaznamy:
    try:
        sig, f, r_r = nacti_zaznam(zaz_id)
        sig_f = preprocess(sig, f)
        r_det = detekuj_r_vrcholy(sig_f, f)
        rr_i  = np.diff(r_det) / f
        tf_i  = 60 / rr_i
        metriky = evaluate_detektor(r_det, r_r, f)
        db_results.append({
            "zaznam":  zaz_id,
            "tf_prumer": tf_i.mean(),
            "tf_std":    tf_i.std(),
            "tf_min":    tf_i.min(),
            "tf_max":    tf_i.max(),
            "Se":        metriky["Se"],
            "F1":        metriky["F1"],
        })
    except Exception as e:
        print(f"Chyba pro {zaz_id}: {e}")

import pandas as pd
df_db = pd.DataFrame(db_results)
print(df_db.to_string(index=False))

# Boxplot TF pro každý záznam
fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(df_db["zaznam"], df_db["tf_prumer"],
       yerr=df_db["tf_std"], capsize=5, color="steelblue", alpha=0.8)
ax.set_xlabel("Záznam"); ax.set_ylabel("Tepová frekvence [BPM]")
ax.set_title("Průměrná tepová frekvence – přehled databáze")
plt.tight_layout(); plt.savefig("tf_databaze.png", dpi=150); plt.show()

# Graf shody (Bland-Altman nebo scatter TF_det vs TF_ref)
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df_db["zaznam"], df_db["Se"]*100, color="tomato",
           s=80, zorder=5, label="Sensitivity [%]")
ax.scatter(df_db["zaznam"], df_db["F1"]*100, color="steelblue",
           s=80, zorder=5, label="F1-skóre [%]")
ax.axhline(95, color="green", linestyle="--", label="95 % práh")
ax.set_ylim(0, 105); ax.set_ylabel("Metrika [%]")
ax.set_title("Shoda detektoru s referenčními anotacemi")
ax.legend(); plt.tight_layout(); plt.savefig("tf_shoda.png", dpi=150); plt.show()
```

### Slabé a silné stránky navrženého detektoru
```
✅ Silné stránky:
  - Pan-Tompkins je standard pro detekci QRS, ověřen na MIT-BIH
  - Band-pass filtr efektivně odstraní baseline drift a EMG šum
  - Adaptivní práh zvládne variabilní amplitudu
  - filtfilt (nulová fáze) nezavádí zpoždění

⚠️ Slabé stránky:
  - Nízká TF (bradykardie): RR > 1.5 s může spadnout mimo min_distance
  - Artefakty pohybu (velké výchylky) mohou být detekovány jako QRS
  - Síňové fibrilace (nepravidelný rytmus): práh nutno přizpůsobit
  - Negativní QRS (inversion): nutno přidat abs() nebo otočit signál
  - Výpočet TF na okrajích (klouzavý průměr) méně přesný
```

---

*Aktualizováno pro státnici – Python (NumPy, SciPy, wfdb, matplotlib)*