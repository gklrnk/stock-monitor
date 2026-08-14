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
    
