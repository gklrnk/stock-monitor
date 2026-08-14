"""
BASKET SERVICE - Koszyk analityczny

Ten modul zarzadza koszykiem - Twoja shortlista max 10 spolek
do glebokiej analizy przed decyzja inwestycyjna.

Kluczowe cechy:
- Maksymalnie 10 spolek w koszyku
- Automatyczny zapis do GitHub (prywatne repo stock-data)
- Synchronizacja miedzy urzadzeniami (komputer/telefon)
- Historia zmian (kiedy dodane, kiedy usuniete)
- Presety - zapisywanie ulubionych zestawow

Uzywane w: pages/basket_page.py
"""

import streamlit as st
from datetime import datetime
from services.github_storage import zapisz_dane, wczytaj_dane


# Limit spolek w koszyku
MAX_BASKET_SIZE = 10

# Nazwa pliku w GitHub
BASKET_FILE = "basket.json"
PRESETS_FILE = "basket_presets.json"


def wczytaj_koszyk():
    """
    Wczytuje aktualny koszyk z GitHub.
    
    Wywolywane przy starcie aplikacji zeby zsynchronizowac
    dane miedzy urzadzeniami.
    
    :return: lista spolek w koszyku
    
    Przyklad zwrotu:
        [
            {
                "ticker": "NVDA",
                "nazwa": "NVIDIA",
                "dodano": "2026-08-11 22:15",
                "notatka": "AI leader"
            },
            ...
        ]
    """
    dane = wczytaj_dane(BASKET_FILE, domyslne={"basket": []})
    return dane.get("basket", [])


def zapisz_koszyk(koszyk):
    """
    Zapisuje koszyk do GitHub.
    
    :param koszyk: lista spolek w koszyku
    :return: True jesli sukces
    """
    dane = {
        "basket": koszyk,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(koszyk)
    }
    return zapisz_dane(BASKET_FILE, dane)


def dodaj_do_koszyka(ticker, nazwa, notatka=""):
    """
    Dodaje spolke do koszyka.
    
    :param ticker: symbol np. "NVDA"
    :param nazwa: pelna nazwa np. "NVIDIA"
    :param notatka: opcjonalna notatka
    :return: (bool, str) - (czy dodano, komunikat)
    """
    # Pobierz aktualny koszyk z session_state
    koszyk = st.session_state.get("basket", [])
    
    # Sprawdz czy juz jest
    if any(item["ticker"] == ticker for item in koszyk):
        return False, f"{ticker} juz jest w koszyku"
    
    # Sprawdz limit
    if len(koszyk) >= MAX_BASKET_SIZE:
        return False, f"Koszyk pelny ({MAX_BASKET_SIZE}/{MAX_BASKET_SIZE}). Usun cos zeby dodac."
    
    # Dodaj
    nowa_pozycja = {
        "ticker": ticker,
        "nazwa": nazwa,
        "dodano": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "notatka": notatka
    }
    koszyk.append(nowa_pozycja)
    
    # Zapisz w session_state
    st.session_state.basket = koszyk
    
    # Zapisz do GitHub (automatyczna synchronizacja)
    zapisz_koszyk(koszyk)
    
    return True, f"Dodano {ticker} do koszyka ({len(koszyk)}/{MAX_BASKET_SIZE})"


def usun_z_koszyka(ticker):
    """
    
