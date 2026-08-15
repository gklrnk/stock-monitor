"""
SESSION STATE - Zarzadzanie stanem aplikacji

Streamlit przy kazdej interakcji uruchamia skrypt od nowa.
Zeby nie tracic danych (wynikow analizy, koszyka, ustawien)
trzymamy je w st.session_state.

Ten modul:
- inicjalizuje wszystkie klucze przy starcie
- wczytuje koszyk z GitHub / dysku (synchronizacja miedzy urzadzeniami)
- daje pomocnicze funkcje do listy obserwowanych spolek

Uzywane w: app.py oraz we wszystkich zakladkach z views/
"""

import streamlit as st
from datetime import datetime

from config.universe import UNIVERSE_DEFAULT
from services.basket_service import wczytaj_koszyk


# Domyslne wartosci wszystkich kluczy sesji
DOMYSLNE = {
    "UNIVERSE": None,          # slownik grup spolek (GPW / GLOBAL / MOJE)
    "df": None,                # DataFrame z analiza obserwowanych
    "last_scan": None,         # data ostatniej analizy
    "scanner_df": None,        # DataFrame ze skanera okazji
    "scanner_last": None,      # data ostatniego skanu
    "news_cache": None,        # cache newsow {ticker: {...}}
    "basket": None,            # koszyk analityczny (max 10 spolek)
    "basket_loaded": False,    # czy koszyk zostal juz wczytany ze storage
    "run_scan": False,         # flaga: uruchom analize obserwowanych
    "run_scanner": None,       # flaga: "quick" / "full" / None
    "portfolio_cache": None,   # cache wyceny portfela
}


def init_session():
    """
    Inicjalizuje wszystkie klucze sesji. Wywolywane RAZ na starcie app.py.

    Bezpieczne do wielokrotnego wywolania - nie nadpisuje istniejacych danych.
    """
    for klucz, wartosc in DOMYSLNE.items():
        if klucz not in st.session_state:
            st.session_state[klucz] = wartosc

    # Uniwersum spolek - kopia glebsza zeby nie modyfikowac stalej
    if st.session_state.UNIVERSE is None:
        st.session_state.UNIVERSE = {
            grupa: dict(spolki) for grupa, spolki in UNIVERSE_DEFAULT.items()
        }

    if st.session_state.news_cache is None:
        st.session_state.news_cache = {}

    if st.session_state.basket is None:
        st.session_state.basket = []

    # Koszyk wczytujemy ze storage tylko raz na sesje
    if not st.session_state.basket_loaded:
        try:
            st.session_state.basket = wczytaj_koszyk()
        except Exception:
            st.session_state.basket = []
        st.session_state.basket_loaded = True


# ========== OBSERWOWANE SPOLKI ==========

def get_all_tickers():
    """
    Zwraca plaski slownik WSZYSTKICH obserwowanych spolek.

    :return: {"PKO.WA": "PKO BP", "NVDA": "NVIDIA", ...}
    """
    wszystkie = {}
    for grupa in st.session_state.UNIVERSE.values():
        wszystkie.update(grupa)
    return wszystkie


def dodaj_do_obserwowanych(ticker, nazwa):
    """
    Dodaje spolke do grupy "MOJE" na liscie obserwowanych.

    :return: (bool, str)
    """
    ticker = ticker.upper().strip()
    wszystkie = get_all_tickers()

    if ticker in wszystkie:
        return False, f"{ticker} jest juz obserwowane ({wszystkie[ticker]})"

    st.session_state.UNIVERSE["MOJE"][ticker] = nazwa or ticker
    return True, f"Dodano {ticker} do obserwowanych"


def usun_z_obserwowanych(ticker):
    """
    Usuwa spolke z listy obserwowanych (z dowolnej grupy).

    :return: (bool, str)
    """
    for grupa in st.session_state.UNIVERSE.values():
        if ticker in grupa:
            del grupa[ticker]
            return True, f"Usunieto {ticker} z obserwowanych"
    return False, f"{ticker} nie jest obserwowane"


def nazwa_spolki(ticker):
    """Zwraca nazwe spolki z listy obserwowanych lub sam ticker."""
    return get_all_tickers().get(ticker, ticker)


# ========== ZNACZNIKI CZASU ==========

def oznacz_analize():
    """Zapisuje date ostatniej analizy obserwowanych."""
    st.session_state.last_scan = datetime.now().strftime("%Y-%m-%d %H:%M")


def oznacz_skan():
    """Zapisuje date ostatniego skanu okazji."""
    st.session_state.scanner_last = datetime.now().strftime("%Y-%m-%d %H:%M")


def reset_wynikow():
    """Czysci wyniki analizy i skanera (np. po duzej zmianie listy spolek)."""
    st.session_state.df = None
    st.session_state.scanner_df = None
    st.session_state.last_scan = None
    st.session_state.scanner_last = None
