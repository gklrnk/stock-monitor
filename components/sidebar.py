"""
SIDEBAR - Panel boczny aplikacji

Zawiera:
- przyciski uruchamiajace analize i skanowanie
- dodawanie / usuwanie obserwowanych spolek
- licznik koszyka
- status magazynu danych (GitHub lub dysk lokalny)

Uzywane w: app.py
"""

import time

import streamlit as st
import yfinance as yf

from services import github_storage
from services.basket_service import MAX_BASKET_SIZE, liczba_w_koszyku
from utils.session_state import (
    get_all_tickers, dodaj_do_obserwowanych, usun_z_obserwowanych
)


def render_sidebar():
    """Rysuje caly panel boczny."""
    with st.sidebar:
        st.markdown("# 📊 Stock Monitor")
        st.markdown("---")

        _sekcja_akcje()
        st.markdown("---")
        _sekcja_dodaj()
        _sekcja_usun()
        st.markdown("---")
        _sekcja_status()


def _sekcja_akcje():
    """Przyciski uruchamiajace analize i skanery."""
    st.markdown("### 🎯 GLOWNE AKCJE")

    if st.button("🔍 Analiza obserwowanych", type="primary"):
        st.session_state.run_scan = True

    st.markdown("### 🔎 SKANER OKAZJI")
    if st.button("⚡ Szybki skan (~200 spolek)"):
        st.session_state.run_scanner = "quick"
    if st.button("🔬 Pelny skan (~300 spolek)"):
        st.session_state.run_scanner = "full"


def _sekcja_dodaj():
    """Formularz dodawania nowej spolki do obserwowanych."""
    st.markdown("### ➕ Dodaj spolke")

    with st.form("dodaj_form"):
        new_ticker = st.text_input("Ticker (np. AAPL, CCC.WA)")
        new_nazwa = st.text_input("Nazwa (opcjonalnie)")
        submitted = st.form_submit_button("➕ Dodaj")

        if submitted and new_ticker:
            ticker = new_ticker.upper().strip()
            wszystkie = get_all_tickers()

            if ticker in wszystkie:
                st.warning(f"Juz obserwowane: {wszystkie[ticker]}")
            else:
                with st.spinner(f"Sprawdzam {ticker} w Yahoo Finance..."):
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="5d")
                        if hist.empty:
                            st.error(f"Nie znaleziono danych dla {ticker}")
                        else:
                            nazwa = new_nazwa.strip() or (
                                stock.info.get("shortName") or ticker
                            )
                            ok, msg = dodaj_do_obserwowanych(ticker, nazwa)
                            if ok:
                                st.success(f"Dodano: {nazwa}")
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                st.warning(msg)
                    except Exception as e:
                        st.error(f"Blad: {e}")


def _sekcja_usun():
    """Usuwanie spolki z listy obserwowanych."""
    st.markdown("### 🗑️ Usun spolke")
    wszystkie = get_all_tickers()

    if not wszystkie:
        st.caption("Lista obserwowanych jest pusta.")
        return

    do_usuniecia = st.selectbox(
        "Wybierz:",
        [""] + list(wszystkie.keys()),
        format_func=lambda x: f"{x} - {wszystkie.get(x, '')}" if x else "-- wybierz --",
    )

    if st.button("🗑️ Usun") and do_usuniecia:
        ok, msg = usun_z_obserwowanych(do_usuniecia)
        if ok:
            st.success(msg)
            time.sleep(0.8)
            st.rerun()
        else:
            st.warning(msg)


def _sekcja_status():
    """Podsumowanie stanu aplikacji i magazynu danych."""
    wszystkie = get_all_tickers()
    st.info(f"📊 Obserwowanych: **{len(wszystkie)}** spolek")
    st.info(f"⭐ Koszyk: **{liczba_w_koszyku()}/{MAX_BASKET_SIZE}**")

    if st.session_state.get("last_scan"):
        st.caption(f"📅 Ost. analiza: {st.session_state.last_scan}")
    if st.session_state.get("scanner_last"):
        st.caption(f"🔎 Ost. skan: {st.session_state.scanner_last}")

    st.markdown("### 💾 Zapis danych")
    if github_storage.czy_skonfigurowany():
        ok, msg = github_storage.status_polaczenia()
        if ok:
            st.success(f"GitHub: {msg}")
        else:
            st.error(f"GitHub: {msg}")
    else:
        st.warning(
            "Brak tokena GitHub - dane zapisuje lokalnie (folder data/). "
            "Dodaj token w Streamlit Secrets, zeby synchronizowac koszyk "
            "i portfolio miedzy urzadzeniami."
        )
