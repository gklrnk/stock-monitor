# 📊 Stock Monitor

Aplikacja do monitorowania spółek z GPW, USA i Europy: analiza fundamentalno-techniczna
ze scoringiem i rekomendacją (KUPUJ / OBSERWUJ / TRZYMAJ / OSTROŻNIE / UNIKAJ),
skaner okazji, koszyk analityczny (shortlista max 10 spółek) i portfolio tracker.

> ⚠️ Narzędzie edukacyjne. Nie stanowi porady inwestycyjnej.
> Dane: Yahoo Finance (opóźnienie ok. 15–20 min, GPW zwykle EOD). Źródło bezpłatne.

---

## 🚀 Uruchomienie w 3 krokach

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikacja otworzy się pod adresem `http://localhost:8501`.

Działa od razu, bez żadnej konfiguracji — koszyk i portfolio zapisują się
lokalnie w folderze `data/`.

---

## 🏗️ Architektura serwisowa

Zasada: **jeden serwis = jeden plik**. Chcesz zmienić scoring? Edytujesz tylko
`services/analysis_service.py`. Chcesz inny wygląd zakładki? Tylko plik w `views/`.
Żaden plik nie ma tysięcy linii i nic nie jest zduplikowane.

```
stock-monitor/
├── app.py                       # ~90 linii - tylko składa aplikację z modułów
├── requirements.txt
│
├── config/
│   └── universe.py              # LISTY SPÓŁEK - tu dodajesz/usuwasz spółki
│
├── services/                    # LOGIKA (bez UI, łatwe do testowania)
│   ├── indicators.py            # RSI, SMA, MACD, zmiany procentowe
│   ├── analysis_service.py      # pełna analiza + scoring 0-100% + sygnał
│   ├── scanner_service.py       # lekka analiza do skanu 300 spółek
│   ├── runner_service.py        # przebiegi wsadowe + pasek postępu
│   ├── news_service.py          # newsy z Yahoo + cache 1h
│   ├── calendar_service.py      # wyniki finansowe i dywidendy
│   ├── basket_service.py        # koszyk analityczny + presety
│   ├── portfolio_service.py     # transakcje, pozycje, FIFO, statystyki
│   ├── chart_service.py         # wykresy Plotly
│   ├── export_service.py        # eksport CSV / Excel
│   ├── github_storage.py        # zapis do prywatnego repo GitHub
│   └── local_storage.py         # zapis lokalny (fallback bez tokena)
│
├── views/                       # ZAKŁADKI (tylko wyświetlanie)
│   ├── observed_view.py         # 📊 Obserwowane
│   ├── scanner_view.py          # 🔎 Skaner okazji
│   ├── basket_view.py           # ⭐ Koszyk
│   ├── portfolio_view.py        # 💼 Portfolio
│   └── calendar_view.py         # 📅 Kalendarz
│
├── components/                  # WSPÓLNE ELEMENTY UI
│   ├── sidebar.py               # panel boczny
│   └── stock_card.py            # karta spółki (używana w kilku miejscach)
│
└── utils/
    ├── session_state.py         # stan aplikacji, lista obserwowanych
    └── formatting.py            # formatowanie liczb, kolory, etykiety
```

### Przepływ zależności

```
app.py  →  views/  →  services/  →  config/
              ↓           ↓
        components/    utils/
```

Serwisy **nie znają** widoków — dzięki temu można je używać poza Streamlitem
(np. w skrypcie generującym raport nocny lub w cronie).

---

## 🧩 Zakładki

| Zakładka | Co robi |
|---|---|
| 📊 **Obserwowane** | Pełna analiza listy obserwowanych: scoring 0–100%, sygnał, zmiany 1T/1M/3M/6M/1R, fundamenty, rekomendacje analityków, wykresy, głęboka analiza pojedynczej spółki, eksport |
| 🔎 **Skaner okazji** | Skan 170–310 spółek w 7 przekrojach: wzrosty, spadki, wolumen, 52W High, 52W Low, tanie fundamentalnie, momentum |
| ⭐ **Koszyk** | Shortlista max 10 spółek: notatki, analiza porównawcza, wykresy, porównanie stóp zwrotu, wspólny feed newsów, presety |
| 💼 **Portfolio** | Transakcje kupna/sprzedaży, pozycje z wyceną real-time, zysk niezrealizowany i zrealizowany (FIFO), win rate, historia, eksport |
| 📅 **Kalendarz** | Nadchodzące wyniki finansowe i dywidendy dla obserwowanych lub koszyka |

---

## 📈 Jak liczony jest scoring

`services/analysis_service.py` przyznaje punkty w kategoriach i przelicza je
na procent maksymalnej możliwej liczby punktów (pomijając brakujące dane):

| Obszar | Wskaźniki |
|---|---|
| Wycena | P/E, P/BV |
| Rentowność | ROE, marża zysku |
| Wypłaty | stopa dywidendy |
| Bezpieczeństwo | zadłużenie / kapitał |
| Wzrost | dynamika przychodów |
| Rynek | rekomendacje analityków, potencjał do ceny docelowej |
| Technika | RSI, MACD, pozycja względem SMA200 |
| Momentum | zmiana 1M i 3M |

Progi sygnałów: **≥70% KUPUJ**, **≥55% OBSERWUJ**, **≥40% TRZYMAJ**,
**≥25% OSTROŻNIE**, poniżej **UNIKAJ**.

Chcesz inne wagi lub progi? To jedna funkcja w jednym pliku.

---

## 💾 Zapis danych (koszyk i portfolio)

**Tryb domyślny — lokalny.** Bez żadnej konfiguracji dane lądują w `data/*.json`.

**Tryb synchronizacji — GitHub.** Aby widzieć ten sam koszyk na komputerze i telefonie:

1. Utwórz **prywatne** repo, np. `stock-data`.
2. Wygeneruj Personal Access Token (scope `repo`).
3. Uzupełnij `.streamlit/secrets.toml` (wzór w `.streamlit/secrets.toml.example`):

```toml
[github]
token = "github_pat_..."
username = "twoj-login"
data_repo = "stock-data"
```

W Streamlit Cloud tę samą treść wklejasz w *Settings → Secrets*.
Aplikacja **sama wykrywa** obecność tokena — kod widoków się nie zmienia.
Status widać na dole panelu bocznego.

Pliki danych: `basket.json`, `basket_presets.json`, `transactions.json`.

---

## ➕ Jak coś zmienić

| Chcę... | Edytuję |
|---|---|
| dodać/usunąć spółkę na stałe | `config/universe.py` |
| zmienić wagi lub progi scoringu | `services/analysis_service.py` |
| dodać nowy filtr do skanera | `views/scanner_view.py` (+ pole w `scanner_service.py`) |
| zmienić wygląd wykresów | `services/chart_service.py` |
| zmienić wygląd karty spółki | `components/stock_card.py` |
| dodać nową zakładkę | nowy plik w `views/` + jedna linia w `ZAKLADKI` w `app.py` |
| zmienić sposób zapisu danych | `services/github_storage.py` lub `local_storage.py` |

Spółkę można też dodać tymczasowo (na czas sesji) z panelu bocznego.

---

## 🔎 Weryfikacja tickerów

Wszystkie 78 spółek obserwowanych zostało sprawdzonych — każda zwraca dane z Yahoo.
Z uniwersum skanera usunięto symbole bez notowań, a zmienione tickery zaktualizowano:

| Było | Jest | Powód |
|---|---|---|
| `SQ` | `XYZ` | Block zmienił ticker |
| `STLA.MI` | `STLAM.MI` | poprawny symbol Stellantis na Borsa Italiana |
| `STM.PA` | `STMPA.PA` | poprawny symbol STMicroelectronics w Paryżu |
| `BML.WA` | `BMC.WA` | poprawny symbol Bumech |

Usunięto (brak danych w Yahoo): `CCC.WA`, `CIE.WA`, `GNB.WA`, `LTS.WA`, `ORB.WA`,
`QMK.WA`, `STL.WA`, `1COV.DE`, `ROG.SW`, `EDF.PA`, `GLPG.AS`, `MMC`.

---

## ⏱️ Ile trwa skanowanie

Między zapytaniami jest celowa przerwa (ochrona przed limitami Yahoo):

- analiza obserwowanych (~78 spółek): **ok. 2–4 min**
- szybki skan (~170 spółek): **ok. 5–8 min**
- pełny skan (~310 spółek): **ok. 10–15 min**

Tempo zmienisz w `services/runner_service.py` (`PAUZA_ANALIZA`, `PAUZA_SKANER`).

---

## ☁️ Wdrożenie na Streamlit Cloud

1. Wrzuć repozytorium na GitHub.
2. share.streamlit.io → *New app* → wskaż repo i `app.py`.
3. Dodaj sekcję `[github]` w *Secrets* (opcjonalnie, dla synchronizacji).

`.gitignore` pilnuje, żeby `secrets.toml` i folder `data/` nie trafiły do repo.
