"""
STOCK CARD - Wielokrotnie uzywana karta spolki

Jedna karta = jeden wiersz wyniku (w skanerze, koszyku, obserwowanych)
z przyciskami: newsy, dodaj do obserwowanych, dodaj do koszyka.

Dzieki wydzieleniu tutaj kazda zakladka wyglada spojnie,
a zmiana wygladu karty to zmiana w jednym pliku.

Uzywane w: views/scanner_view.py, views/basket_view.py
"""

import time

import pandas as pd
import streamlit as st

from services.basket_service import czy_w_koszyku, dodaj_do_koszyka
from services.news_service import pobierz_newsy
from utils.formatting import badge_zmiany
from utils.session_state import get_all_tickers, dodaj_do_obserwowanych


def render_karta(row, kolumny_extra, tab_id="tab", idx=0,
                 pokaz_obserwuj=True, pokaz_koszyk=True):
    """
    Rysuje pojedyncza karte spolki.

    :param row: wiersz DataFrame (Series) z co najmniej Ticker/Nazwa/Rynek/Cena
    :param kolumny_extra: lista par (klucz, etykieta) do pokazania
    :param tab_id: unikalny prefiks kluczy przyciskow (wymagany przez Streamlit)
    :param idx: indeks wiersza - czesc klucza przycisku
    :param pokaz_obserwuj: czy pokazac przycisk dodania do obserwowanych
    :param pokaz_koszyk: czy pokazac przycisk dodania do koszyka
    """
    ticker = row["Ticker"]
    nazwa = row.get("Nazwa", ticker)

    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])

    with col1:
        st.markdown(f"**{nazwa}** ({ticker})")
        st.caption(f"Rynek: {row.get('Rynek', '-')} | Cena: {row.get('Cena', '-')}")

    with col2:
        _render_metryki(row, kolumny_extra[:2])

    with col3:
        _render_metryki(row, kolumny_extra[2:4])

    with col4:
        _render_przyciski(row, ticker, nazwa, tab_id, idx,
                          pokaz_obserwuj, pokaz_koszyk)

    _render_newsy(ticker, nazwa, tab_id, idx)
    st.markdown("---")


def _render_metryki(row, pary):
    """Wyswietla male metryki (procenty na kolorowo)."""
    for klucz, etykieta in pary:
        if klucz not in row:
            continue
        val = row[klucz]
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        if "%" in etykieta:
            st.markdown(badge_zmiany(etykieta, val), unsafe_allow_html=True)
        else:
            st.markdown(f"<small>{etykieta}: <b>{val}</b></small>",
                        unsafe_allow_html=True)


def _render_przyciski(row, ticker, nazwa, tab_id, idx, pokaz_obserwuj, pokaz_koszyk):
    """Przyciski akcji: newsy / obserwuj / koszyk."""
    b1, b2 = st.columns(2)

    with b1:
        if st.button("📰 News", key=f"news_{tab_id}_{ticker}_{idx}"):
            st.session_state[f"show_news_{tab_id}_{ticker}"] = True

    with b2:
        if pokaz_obserwuj:
            if ticker in get_all_tickers():
                st.caption("✅ obserwowane")
            elif st.button("➕ Obserwuj", key=f"obs_{tab_id}_{ticker}_{idx}"):
                ok, msg = dodaj_do_obserwowanych(ticker, nazwa)
                if ok:
                    st.success(msg)
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.warning(msg)

    if pokaz_koszyk:
        if czy_w_koszyku(ticker):
            st.caption("⭐ w koszyku")
        elif st.button("⭐ Do koszyka", key=f"kosz_{tab_id}_{ticker}_{idx}"):
            ok, msg = dodaj_do_koszyka(ticker, nazwa)
            if ok:
                st.success(msg)
                time.sleep(0.6)
                st.rerun()
            else:
                st.warning(msg)


def _render_newsy(ticker, nazwa, tab_id, idx):
    """Rozwijany panel z newsami dla spolki."""
    if not st.session_state.get(f"show_news_{tab_id}_{ticker}"):
        return

    with st.expander(f"📰 Newsy: {nazwa}", expanded=True):
        with st.spinner("Pobieram newsy..."):
            newsy = pobierz_newsy(ticker)

        if newsy:
            for n in newsy:
                st.markdown(f"**{n['date']}** | *{n['publisher']}*")
                st.markdown(f"[{n['title']}]({n['link']})")
                st.markdown("---")
        else:
            st.info("Brak dostepnych newsow dla tej spolki.")

        if st.button("✖️ Zamknij", key=f"close_{tab_id}_{ticker}_{idx}"):
            st.session_state[f"show_news_{tab_id}_{ticker}"] = False
            st.rerun()
