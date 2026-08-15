"""
STOCK MONITOR - Punkt wejscia aplikacji

Ten plik jest CELOWO krotki. Nie ma tu logiki biznesowej ani widokow:
- dane i obliczenia  -> services/
- wyglad zakladek    -> views/
- wspolne elementy   -> components/
- stan i pomocnicze  -> utils/
- lista spolek       -> config/universe.py

Uruchomienie:
    streamlit run app.py
"""

import warnings

import streamlit as st

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Stock Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from components.sidebar import render_sidebar          # noqa: E402
from utils.session_state import init_session           # noqa: E402
from views import (                                    # noqa: E402
    observed_view, scanner_view, calendar_view,
    basket_view, portfolio_view,
)

STYL = """
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 12px;
        border-radius: 10px;
        border-left: 4px solid #1e3c72;
    }
</style>
"""

# Kolejnosc zakladek = kolejnosc pracy: analiza -> szukanie -> shortlista -> portfel
ZAKLADKI = [
    ("📊 Obserwowane", observed_view),
    ("🔎 Skaner okazji", scanner_view),
    ("⭐ Koszyk", basket_view),
    ("💼 Portfolio", portfolio_view),
    ("📅 Kalendarz", calendar_view),
]


def main():
    """Sklada aplikacje z gotowych modulow."""
    st.markdown(STYL, unsafe_allow_html=True)

    init_session()
    render_sidebar()

    st.markdown('<div class="main-title">📊 STOCK MONITOR</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:gray;'>"
        "Monitor + skaner okazji + koszyk analityczny + portfolio | "
        "GPW / USA / Europa</p>",
        unsafe_allow_html=True,
    )

    for tab, (_, modul) in zip(st.tabs([n for n, _ in ZAKLADKI]), ZAKLADKI):
        with tab:
            modul.render()

    st.markdown("---")
    st.caption(
        "⚠️ Narzedzie edukacyjne. Nie stanowi porady inwestycyjnej. "
        "Zrodlo danych: Yahoo Finance (opoznienie ok. 15-20 min, GPW zwykle EOD)."
    )


if __name__ == "__main__":
    main()
