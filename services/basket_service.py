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
    Usuwa spolke z koszyka.
    
    :param ticker: symbol do usuniecia
    :return: (bool, str)
    """
    koszyk = st.session_state.get("basket", [])
    
    # Znajdz i usun
    nowy_koszyk = [item for item in koszyk if item["ticker"] != ticker]
    
    if len(nowy_koszyk) == len(koszyk):
        return False, f"{ticker} nie jest w koszyku"
    
    st.session_state.basket = nowy_koszyk
    zapisz_koszyk(nowy_koszyk)
    
    return True, f"Usunieto {ticker} z koszyka"


def wyczysc_koszyk():
    """
    Czysci caly koszyk.
    
    :return: True jesli sukces
    """
    st.session_state.basket = []
    zapisz_koszyk([])
    return True


def zamien_w_koszyku(stary_ticker, nowy_ticker, nowa_nazwa):
    """
    Zamienia jedna spolke na inna (zachowuje pozycje w liscie).
    
    Przydatne gdy chcesz podmienic np. AMD na NVDA bez usuwania
    i dodawania.
    
    :return: (bool, str)
    """
    koszyk = st.session_state.get("basket", [])
    
    for i, item in enumerate(koszyk):
        if item["ticker"] == stary_ticker:
            koszyk[i] = {
                "ticker": nowy_ticker,
                "nazwa": nowa_nazwa,
                "dodano": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "notatka": item.get("notatka", "")
            }
            st.session_state.basket = koszyk
            zapisz_koszyk(koszyk)
            return True, f"Zamieniono {stary_ticker} na {nowy_ticker}"
    
    return False, f"{stary_ticker} nie jest w koszyku"


def aktualizuj_notatke(ticker, nowa_notatka):
    """
    Aktualizuje notatke dla spolki w koszyku.
    
    :return: (bool, str)
    """
    koszyk = st.session_state.get("basket", [])
    
    for item in koszyk:
        if item["ticker"] == ticker:
            item["notatka"] = nowa_notatka
            st.session_state.basket = koszyk
            zapisz_koszyk(koszyk)
            return True, "Notatka zapisana"
    
    return False, f"{ticker} nie jest w koszyku"


def czy_w_koszyku(ticker):
    """
    Sprawdza czy spolka jest w koszyku.
    
    Uzywane w skanerze do pokazania odpowiedniego przycisku
    (Dodaj vs W koszyku).
    
    :param ticker: symbol
    :return: True/False
    """
    koszyk = st.session_state.get("basket", [])
    return any(item["ticker"] == ticker for item in koszyk)


def pobierz_tickery_z_koszyka():
    """
    Zwraca liste samych tickerow z koszyka.
    
    Uzywane do pobrania newsow lub analizy porownawczej.
    
    :return: lista tickerow np. ["NVDA", "CDR.WA", "MSFT"]
    """
    koszyk = st.session_state.get("basket", [])
    return [item["ticker"] for item in koszyk]


def liczba_w_koszyku():
    """
    Zwraca liczbe spolek w koszyku.
    
    Uzywane w sidebar do pokazania licznika "5/10".
    
    :return: int
    """
    return len(st.session_state.get("basket", []))


# ========== PRESETY (zapisane koszyki) ==========

def wczytaj_presety():
    """
    Wczytuje wszystkie zapisane presety z GitHub.
    
    :return: slownik z presetami
    
    Przyklad:
        {
            "banki_gpw": {"tickers": ["PKO.WA", "PEO.WA"], "created": "..."},
            "ai_stocks": {"tickers": ["NVDA", "AMD"], "created": "..."}
        }
    """
    dane = wczytaj_dane(PRESETS_FILE, domyslne={"presets": {}})
    return dane.get("presets", {})


def zapisz_preset(nazwa, koszyk=None):
    """
    Zapisuje aktualny koszyk jako preset pod nazwa.
    
    :param nazwa: nazwa presetu np. "banki_gpw"
    :param koszyk: opcjonalny koszyk (domyslnie: aktualny z session)
    :return: (bool, str)
    """
    if koszyk is None:
        koszyk = st.session_state.get("basket", [])
    
    if not koszyk:
        return False, "Koszyk jest pusty - nic do zapisania"
    
    # Pobierz obecne presety
    presety = wczytaj_presety()
    
    # Dodaj nowy
    presety[nazwa] = {
        "basket": koszyk,
        "count": len(koszyk),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # Zapisz do GitHub
    zapisz_dane(PRESETS_FILE, {"presets": presety})
    
    return True, f"Zapisano preset '{nazwa}' ({len(koszyk)} spolek)"


def wczytaj_preset(nazwa):
    """
    Wczytuje preset i podstawia jako aktualny koszyk.
    
    :param nazwa: nazwa presetu
    :return: (bool, str)
    """
    presety = wczytaj_presety()
    
    if nazwa not in presety:
        return False, f"Preset '{nazwa}' nie istnieje"
    
    koszyk = presety[nazwa].get("basket", [])
    st.session_state.basket = koszyk
    zapisz_koszyk(koszyk)
    
    return True, f"Wczytano preset '{nazwa}' ({len(koszyk)} spolek)"


def usun_preset(nazwa):
    """
    Usuwa preset z listy.
    
    :param nazwa: nazwa presetu
    :return: (bool, str)
    """
    presety = wczytaj_presety()
    
    if nazwa not in presety:
        return False, f"Preset '{nazwa}' nie istnieje"
    
    del presety[nazwa]
    zapisz_dane(PRESETS_FILE, {"presets": presety})
    
    return True, f"Usunieto preset '{nazwa}'"
