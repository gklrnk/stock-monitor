"""
CALENDAR VIEW - Zakladka "Kalendarz wydarzen"

Pokazuje nadchodzace wyniki finansowe i dywidendy dla spolek
obserwowanych oraz dla spolek z koszyka.

Logika pobierania siedzi w services/calendar_service.py.
"""

import pandas as pd
import streamlit as st

from services.basket_service import pobierz_tickery_z_koszyka
from services.calendar_service import pobierz_pelny_kalendarz, formatuj_dni_do
from utils.session_state import get_all_tickers


def render():
    """Punkt wejscia zakladki."""
    st.markdown("### 📅 Kalendarz wydarzen")
    st.caption("Publikacja wynikow i dywidendy potrafia mocno ruszyc kursem.")

    zrodlo = st.radio("Dla ktorych spolek:",
                      ["Obserwowane", "Koszyk analityczny"],
                      horizontal=True, key="cal_zrodlo")
    dni = st.slider("Horyzont (dni)", 7, 60, 14, step=7, key="cal_dni")

    tickery = (list(get_all_tickers().keys()) if zrodlo == "Obserwowane"
               else pobierz_tickery_z_koszyka())

    if not tickery:
        st.info("Brak spolek w wybranym zrodle.")
        return

    st.caption(f"Sprawdzam {len(tickery)} spolek.")

    if not st.button("🔄 Sprawdz nadchodzace wydarzenia", key="cal_run"):
        st.info("Kliknij przycisk, aby pobrac kalendarz "
                "(pobranie kilkudziesieciu spolek trwa chwile).")
        return

    with st.spinner("Pobieram kalendarze z Yahoo Finance..."):
        kalendarz = pobierz_pelny_kalendarz(tickery, dni=dni)

    _podsumowanie(kalendarz, dni)
    _sekcja_wyniki(kalendarz["wyniki"])
    _sekcja_dywidendy(kalendarz["dywidendy"])


def _podsumowanie(kalendarz, dni):
    """Metryki na gorze zakladki."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Wydarzen razem", kalendarz["razem"])
    c2.metric("Wyniki finansowe", len(kalendarz["wyniki"]))
    c3.metric("Dywidendy", len(kalendarz["dywidendy"]))

    if kalendarz["najblizsze_dni"] is not None:
        st.info(f"Najblizsze wydarzenie: {formatuj_dni_do(kalendarz['najblizsze_dni'])}")
    else:
        st.info(f"Brak zaplanowanych wydarzen w ciagu {dni} dni.")


def _sekcja_wyniki(wyniki):
    """Lista nadchodzacych publikacji wynikow."""
    st.markdown("#### 📊 Wyniki finansowe")
    if not wyniki:
        st.caption("Brak zaplanowanych publikacji wynikow.")
        return

    for w in wyniki:
        st.markdown(
            f"**{w['Data']}** {formatuj_dni_do(w['Dni_do'])} | "
            f"{w['Nazwa']} ({w['Ticker']})"
        )
    st.dataframe(pd.DataFrame(wyniki), width="stretch")


def _sekcja_dywidendy(dywidendy):
    """Lista nadchodzacych dywidend."""
    st.markdown("#### 💰 Dywidendy")
    if not dywidendy:
        st.caption("Brak nadchodzacych dywidend.")
        return

    for d in dywidendy:
        st.markdown(
            f"**{d['Data']}** {formatuj_dni_do(d['Dni_do'])} | "
            f"{d['Nazwa']} ({d['Ticker']}) | "
            f"{d.get('Kwota', '-')} {d.get('Waluta', '')} "
            f"({d.get('Yield%', '-')}%)"
        )
    st.dataframe(pd.DataFrame(dywidendy), width="stretch")
