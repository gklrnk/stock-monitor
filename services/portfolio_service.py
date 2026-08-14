"""
PORTFOLIO SERVICE - Zarzadzanie portfelem inwestycyjnym

Ten modul obsluguje kompletny portfolio tracker:
- Dodawanie transakcji (kupno/sprzedaz)
- Obliczanie aktualnych pozycji
- Wycena real-time z Yahoo Finance
- Historia wszystkich operacji
- Statystyki (zysk, win rate, ROI)

Dane sa zapisywane do prywatnego repo GitHub:
- transactions.json - historia wszystkich transakcji
- portfolio.json - aktualne pozycje (obliczane)

Uzywane w: pages/portfolio_page.py
"""

import yfinance as yf
from datetime import datetime
from services.github_storage import zapisz_dane, wczytaj_dane


# Nazwy plikow w GitHub
TRANSACTIONS_FILE = "transactions.json"


# ========== WCZYTYWANIE / ZAPIS ==========

def wczytaj_transakcje():
    """
    Wczytuje historie wszystkich transakcji z GitHub.
    
    :return: lista transakcji
    
    Przyklad zwrotu:
        [
            {
                "id": "20260811_221500",
                "typ": "KUPNO",
                "ticker": "NVDA",
                "nazwa": "NVIDIA",
                "ilosc": 10,
                "cena": 920.50,
                "prowizja": 0,
                "waluta": "USD",
                "data": "2026-08-11",
                "notatka": "Zakup po dobrych wynikach"
            },
            ...
        ]
    """
    dane = wczytaj_dane(TRANSACTIONS_FILE, domyslne={"transactions": []})
    return dane.get("transactions", [])


def zapisz_transakcje(transakcje):
    """
    Zapisuje transakcje do GitHub.
    
    :param transakcje: lista wszystkich transakcji
    :return: True jesli sukces
    """
    dane = {
        "transactions": transakcje,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(transakcje)
    }
    return zapisz_dane(TRANSACTIONS_FILE, dane)


# ========== DODAWANIE TRANSAKCJI ==========

def dodaj_transakcje(typ, ticker, nazwa, ilosc, cena, data=None, prowizja=0, waluta="PLN", notatka=""):
    """
    Dodaje nowa transakcje (kupno lub sprzedaz).
    
    :param typ: "KUPNO" lub "SPRZEDAZ"
    :param ticker: symbol np. "NVDA"
    :param nazwa: pelna nazwa
    :param ilosc: liczba akcji
    :param cena: cena za akcje
    :param data: data transakcji (domyslnie dzisiaj)
    :param prowizja: opcjonalna prowizja maklerska
    :param waluta: PLN, USD, EUR, GBP
    :param notatka: opcjonalny komentarz
    :return: (bool, str)
    """
    # Walidacja
    if typ not in ["KUPNO", "SPRZEDAZ"]:
        return False, "Typ musi byc KUPNO lub SPRZEDAZ"
    
    if ilosc <= 0:
        return False, "Ilosc musi byc wieksza niz 0"
    
    if cena <= 0:
        return False, "Cena musi byc wieksza niz 0"
    
    # Jesli sprzedaz - sprawdz czy mamy tyle akcji
    if typ == "SPRZEDAZ":
        pozycja = pobierz_pozycje(ticker)
        if pozycja is None or pozycja["ilosc"] < ilosc:
            posiadane = pozycja["ilosc"] if pozycja else 0
            return False, f"Nie masz tylu akcji {ticker} (masz {posiadane}, chcesz sprzedac {ilosc})"
    
    # Utworz transakcje
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    
    id_transakcji = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    nowa_transakcja = {
        "id": id_transakcji,
        "typ": typ,
        "ticker": ticker.upper(),
        "nazwa": nazwa,
        "ilosc": int(ilosc),
        "cena": round(float(cena), 2),
        "prowizja": round(float(prowizja), 2),
        "waluta": waluta,
        "data": data,
        "wartosc": round(float(ilosc) * float(cena), 2),
        "notatka": notatka
    }
    
    # Wczytaj obecne, dodaj nowa, zapisz
    transakcje = wczytaj_transakcje()
    transakcje.append(nowa_transakcja)
    
    if zapisz_transakcje(transakcje):
        return True, f"Dodano {typ} {ilosc} akcji {ticker} @ {cena}"
    else:
        return False, "Blad zapisu transakcji"


def usun_transakcje(id_transakcji):
    """
    Usuwa transakcje po ID (do korekt pomylek).
    
    :param id_transakcji: unikalny ID transakcji
    :return: (bool, str)
    """
    transakcje = wczytaj_transakcje()
    nowa_lista = [t for t in transakcje if t["id"] != id_transakcji]
    
    if len(nowa_lista) == len(transakcje):
        return False, "Nie znaleziono transakcji"
    
    zapisz_transakcje(nowa_lista)
    return True, "Transakcja usunieta"


# ========== OBLICZANIE POZYCJI ==========

def pobierz_wszystkie_pozycje():
    """
    Oblicza aktualne pozycje na podstawie historii transakcji.
    
    Dla kazdej spolki liczy:
    - Aktualna ilosc akcji
    - Srednia cena zakupu (weighted average)
    - Zainwestowana kwota
    
    Nie dodaje aktualnych cen z Yahoo - to robi pobierz_pozycje_z_wycena()
    
    :return: lista aktualnych pozycji
    
    Przyklad zwrotu:
        [
            {
                "ticker": "NVDA",
                "nazwa": "NVIDIA",
                "ilosc": 10,
                "srednia_cena": 850.00,
                "zainwestowano": 8500.00,
                "waluta": "USD"
            },
            ...
        ]
    """
    transakcje = wczytaj_transakcje()
    pozycje = {}
    
    for t in transakcje:
        ticker = t["ticker"]
        
        if ticker not in pozycje:
            pozycje[ticker] = {
                "ticker": ticker,
                "nazwa": t["nazwa"],
                "ilosc": 0,
                "zainwestowano": 0,
                "waluta": t["waluta"],
                "liczba_zakupow": 0,
                "liczba_sprzedazy": 0
            }
        
        if t["typ"] == "KUPNO":
            pozycje[ticker]["ilosc"] += t["ilosc"]
            pozycje[ticker]["zainwestowano"] += t["wartosc"] + t["prowizja"]
            pozycje[ticker]["liczba_zakupow"] += 1
        elif t["typ"] == "SPRZEDAZ":
            pozycje[ticker]["ilosc"] -= t["ilosc"]
            pozycje[ticker]["zainwestowano"] -= (t["wartosc"] - t["prowizja"])
            pozycje[ticker]["liczba_sprzedazy"] += 1
    
    # Oblicz srednia cene i odfiltruj zamkniete pozycje
    aktywne = []
    for p in pozycje.values():
        if p["ilosc"] > 0:
            p["srednia_cena"] = round(p["zainwestowano"] / p["ilosc"], 2)
            aktywne.append(p)
    
    return aktywne


def pobierz_pozycje(ticker):
    """
    Zwraca pozycje dla jednej spolki lub None jesli nie ma.
    
    :param ticker: symbol
    :return: slownik z pozycja lub None
    """
    wszystkie = pobierz_wszystkie_pozycje()
    for p in wszystkie:
        if p["ticker"] == ticker.upper():
            return p
    return None


def pobierz_pozycje_z_wycena():
    """
    Pobiera pozycje i dodaje aktualne ceny z Yahoo Finance.
    
    To wersja z pelnymi danymi do wyswietlenia w portfelu.
    
    :return: lista pozycji z wycena i zyskiem
    
    Przyklad zwrotu:
        [
            {
                "ticker": "NVDA",
                "nazwa": "NVIDIA",
                "ilosc": 10,
                "srednia_cena": 850.00,
                "aktualna_cena": 920.50,
                "wartosc_zakupu": 8500.00,
                "wartosc_aktualna": 9205.00,
                "zysk": 705.00,
                "zysk_pct": 8.29,
                "waluta": "USD"
            },
            ...
        ]
    """
    pozycje = pobierz_wszystkie_pozycje()
    
    for p in pozycje:
        try:
            stock = yf.Ticker(p["ticker"])
            hist = stock.history(period="5d")
            
            if not hist.empty:
                aktualna_cena = float(hist["Close"].iloc[-1])
                wartosc_aktualna = round(aktualna_cena * p["ilosc"], 2)
                zysk = round(wartosc_aktualna - p["zainwestowano"], 2)
                zysk_pct = round((zysk / p["zainwestowano"]) * 100, 2) if p["zainwestowano"] > 0 else 0
                
                p["aktualna_cena"] = round(aktualna_cena, 2)
                p["wartosc_aktualna"] = wartosc_aktualna
                p["wartosc_zakupu"] = p["zainwestowano"]
                p["zysk"] = zysk
                p["zysk_pct"] = zysk_pct
            else:
                # Brak danych - podstaw zero
                p["aktualna_cena"] = None
                p["wartosc_aktualna"] = None
                p["wartosc_zakupu"] = p["zainwestowano"]
                p["zysk"] = None
                p["zysk_pct"] = None
        except:
            p["aktualna_cena"] = None
            p["wartosc_aktualna"] = None
            p["wartosc_zakupu"] = p["zainwestowano"]
            p["zysk"] = None
            p["zysk_pct"] = None
    
    return pozycje


# ========== STATYSTYKI PORTFELA ==========

def podsumowanie_portfela():
    """
    Zwraca podsumowanie portfela z kluczowymi metrykami.
    
    :return: slownik z statystykami
    
    Przyklad zwrotu:
        {
            "liczba_pozycji": 5,
            "wartosc_zakupu_total": 40000,
            "wartosc_aktualna_total": 42350,
            "zysk_niezrealizowany": 2350,
            "zysk_niezrealizowany_pct": 5.88,
            "waluta": "PLN"  # dominujaca
        }
    """
    pozycje = pobierz_pozycje_z_wycena()
    
    if not pozycje:
        return {
            "liczba_pozycji": 0,
            "wartosc_zakupu_total": 0,
            "wartosc_aktualna_total": 0,
            "zysk_niezrealizowany": 0,
            "zysk_niezrealizowany_pct": 0,
            "waluta": "PLN"
        }
    
    # Grupowanie po walucie (uproszczone - dominujaca)
    walutowe = {}
    for p in pozycje:
        w = p.get("waluta", "PLN")
        if w not in walutowe:
            walutowe[w] = {"zakup": 0, "aktualna": 0}
        walutowe[w]["zakup"] += p["wartosc_zakupu"] or 0
        walutowe[w]["aktualna"] += p["wartosc_aktualna"] or 0
    
    # Dominujaca waluta
    dominujaca = max(walutowe.keys(), key=lambda w: walutowe[w]["zakup"])
    dane_dom = walutowe[dominujaca]
    
    zysk = dane_dom["aktualna"] - dane_dom["zakup"]
    zysk_pct = (zysk / dane_dom["zakup"] * 100) if dane_dom["zakup"] > 0 else 0
    
    return {
        "liczba_pozycji": len(pozycje),
        "wartosc_zakupu_total": round(dane_dom["zakup"], 2),
        "wartosc_aktualna_total": round(dane_dom["aktualna"], 2),
        "zysk_niezrealizowany": round(zysk, 2),
        "zysk_niezrealizowany_pct": round(zysk_pct, 2),
        "waluta": dominujaca,
        "wszystkie_waluty": walutowe
    }


def zysk_zrealizowany():
    """
    Oblicza zysk/strate z zamknietych pozycji.
    
    Analizuje pary KUPNO-SPRZEDAZ dla kazdej spolki.
    
    :return: lista zrealizowanych transakcji z zyskami
    
    Przyklad zwrotu:
        [
            {
                "ticker": "XTB.WA",
                "nazwa": "XTB",
                "kupno_cena": 35.00,
                "sprzedaz_cena": 38.00,
                "ilosc": 50,
                "zysk": 150.00,
                "zysk_pct": 8.57,
                "data_kupna": "2026-06-01",
                "data_sprzedazy": "2026-07-15"
            },
            ...
        ]
    """
    transakcje = wczytaj_transakcje()
    zrealizowane = []
    
    # Grupuj po tickerze
    po_tickerach = {}
    for t in transakcje:
        ticker = t["ticker"]
        if ticker not in po_tickerach:
            po_tickerach[ticker] = []
        po_tickerach[ticker].append(t)
    
    # Sparuj kupna i sprzedaze (FIFO - First In First Out)
    for ticker, ts in po_tickerach.items():
        # Sortuj chronologicznie
        ts.sort(key=lambda x: x["data"])
        
        kolejka_kupna = []
        
        for t in ts:
            if t["typ"] == "KUPNO":
                kolejka_kupna.append(t.copy())
            elif t["typ"] == "SPRZEDAZ":
                # Sparuj z najstarszymi kupnami (FIFO)
                sprzedane_ilosc = t["ilosc"]
                srednia_cena_kupna = 0
                
                while sprzedane_ilosc > 0 and kolejka_kupna:
                    kupno = kolejka_kupna[0]
                    
                    if kupno["ilosc"] <= sprzedane_ilosc:
                        # Pobierz cala transakcje kupna
                        srednia_cena_kupna += kupno["cena"] * kupno["ilosc"]
                        sprzedane_ilosc -= kupno["ilosc"]
                        kolejka_kupna.pop(0)
                    else:
                        # Czesciowo
                        srednia_cena_kupna += kupno["cena"] * sprzedane_ilosc
                        kupno["ilosc"] -= sprzedane_ilosc
                        sprzedane_ilosc = 0
                
                if t["ilosc"] > sprzedane_ilosc:
                    # Zapisz pare
                    ilosc_zamknieta = t["ilosc"] - sprzedane_ilosc
                    srednia_kupna = srednia_cena_kupna / ilosc_zamknieta if ilosc_zamknieta > 0 else 0
                    
                    zysk = round((t["cena"] - srednia_kupna) * ilosc_zamknieta, 2)
                    zysk_pct = round(((t["cena"] - srednia_kupna) / srednia_kupna) * 100, 2) if srednia_kupna > 0 else 0
                    
                    zrealizowane.append({
                        "ticker": ticker,
                        "nazwa": t["nazwa"],
                        "kupno_cena": round(srednia_kupna, 2),
                        "sprzedaz_cena": t["cena"],
                        "ilosc": ilosc_zamknieta,
                        "zysk": zysk,
                        "zysk_pct": zysk_pct,
                        "data_sprzedazy": t["data"],
                        "waluta": t["waluta"]
                    })
    
    return zrealizowane


def statystyki_zaawansowane():
    """
    Zwraca zaawansowane statystyki portfela.
    
    :return: slownik z metrykami
    """
    pozycje = pobierz_pozycje_z_wycena()
    zrealizowane = zysk_zrealizowany()
    transakcje = wczytaj_transakcje()
    
    # Suma zysku zrealizowanego
    suma_zrealizowanego = sum(z["zysk"] for z in zrealizowane)
    
    # Win rate (procent zyskownych zamknietych pozycji)
    zyskowne = [z for z in zrealizowane if z["zysk"] > 0]
    win_rate = round((len(zyskowne) / len(zrealizowane)) * 100, 1) if zrealizowane else 0
    
    # Najlepsza i najgorsza z otwartych
    najlepsza = None
    najgorsza = None
    if pozycje:
        z_zyskiem = [p for p in pozycje if p.get("zysk_pct") is not None]
        if z_zyskiem:
            najlepsza = max(z_zyskiem, key=lambda x: x["zysk_pct"])
            najgorsza = min(z_zyskiem, key=lambda x: x["zysk_pct"])
    
    return {
        "otwarte_pozycje": len(pozycje),
        "zamkniete_pozycje": len(zrealizowane),
        "total_transakcji": len(transakcje),
        "zysk_zrealizowany": round(suma_zrealizowanego, 2),
        "win_rate": win_rate,
        "zyskowne_transakcje": len(zyskowne),
        "stratne_transakcje": len(zrealizowane) - len(zyskowne),
        "najlepsza_pozycja": najlepsza,
        "najgorsza_pozycja": najgorsza
    }


# ========== POMOCNICZE ==========

def formatuj_walute(kwota, waluta="PLN"):
    """
    Formatuje kwote z symbolem waluty.
    
    :return: string np. "9 205.00 USD"
    """
    if kwota is None:
        return "-"
    
    symbole = {"PLN": "zl", "USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbole.get(waluta, waluta)
    
    return f"{kwota:,.2f} {symbol}"


def format_zysk(zysk, procent=False):
    """
    Formatuje zysk z kolorem (zielony/czerwony) - do markdown.
    
    :return: string z emoji strzalka
    """
    if zysk is None:
        return "-"
    
    if procent:
        return f"{'📈' if zysk > 0 else '📉' if zysk < 0 else '➖'} {zysk:+.2f}%"
    else:
        return f"{'📈' if zysk > 0 else '📉' if zysk < 0 else '➖'} {zysk:+,.2f}"
