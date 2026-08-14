"""
SESSION STATE - Inicjalizacja zmiennych sesji Streamlit

Modul inicjalizuje wszystkie zmienne w st.session_state
przy pierwszym uruchomieniu aplikacji.

Dane koszyka, portfolio i historii transakcji sa wczytywane
z prywatnego repozytorium GitHub tylko raz na sesje.

Uzycie w app.py:

    from utils.session_state import init_session_state

    init_session_state()
"""

import streamlit as st

from services.basket_service import wczytaj_koszyk
from services.portfolio_service import (
    wczytaj_portfolio,
    wczytaj_transakcje,
)


def init_session_state():
    """
    Inicjalizuje zmienne sesji przy pierwszym uruchomieniu.

    Funkcja jest bezpieczna do wielokrotnego wywolania.
    Przy kolejnych uruchomieniach nie nadpisuje danych sesji.
    """

    if st.session_state.get("initialized", False):
        return

    # Dane trwale przechowywane w GitHub
    st.session_state.basket = wczytaj_koszyk()
    st.session_state.portfolio = wczytaj_portfolio()
    st.session_state.transakcje = wczytaj_transakcje()

    # Wybrana spolka
    st.session_state.selected_ticker = None
    st.session_state.selected_nazwa = None

    # Aktywna grupa spolek
    st.session_state.active_group = "GPW"

    # Wyniki skanera
    st.session_state.scanner_results = []
    st.session_state.scanner_last_run = None

    # Cache analiz
    st.session_state.analysis_cache = {}

    # Cache newsow
    st.session_state.news_cache = {}

    # Cache kalendarza makro
    st.session_state.calendar_cache = None
    st.session_state.calendar_last_fetch = None

    # Ostatni komunikat dla uzytkownika
    st.session_state.last_message = None
    st.session_state.last_message_type = None

    # Flaga zakonczenia inicjalizacji
    st.session_state.initialized = True


def reset_session_state():
    """
    Resetuje sesje i ponownie wczytuje dane z GitHub.

    Uzywane np. po kliknieciu przycisku:
    'Odswiez dane z GitHub'.
    """

    st.session_state.initialized = False

    # Usuniecie danych, aby nie pozostaly stare wartosci
    keys_to_remove = [
        "basket",
        "portfolio",
        "transakcje",
        "selected_ticker",
        "selected_nazwa",
        "scanner_results",
        "scanner_last_run",
        "analysis_cache",
        "news_cache",
        "calendar_cache",
        "calendar_last_fetch",
        "last_message",
        "last_message_type",
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)

    init_session_state()


def ustaw_komunikat(tekst, typ="info"):
    """
    Ustawia komunikat do wyswietlenia w interfejsie.

    :param tekst: tresc komunikatu
    :param typ: success, error, warning albo info
    """

    dozwolone_typy = {"success", "error", "warning", "info"}

    if typ not in dozwolone_typy:
        typ = "info"

    st.session_state.last_message = tekst
    st.session_state.last_message_type = typ


def wyswietl_komunikat():
    """
    Wyswietla ostatni komunikat i usuwa go z sesji.

    Funkcje mozna wywolac na poczatku kazdej strony Streamlit.
    """

    tekst = st.session_state.get("last_message")

    if not tekst:
        return

    typ = st.session_state.get("last_message_type", "info")

    if typ == "success":
        st.success(tekst)
    elif typ == "error":
        st.error(tekst)
    elif typ == "warning":
        st.warning(tekst)
    else:
        st.info(tekst)

    st.session_state.last_message = None
    st.session_state.last_message_type = None
