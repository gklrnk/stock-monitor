"""
RUNNER SERVICE - Uruchamianie analiz wsadowych

Ten modul spina pojedyncze analizy (analysis_service / scanner_service)
w przebieg po calej liscie spolek, z paskiem postepu i limitowaniem
tempa zapytan do Yahoo Finance.

Widoki nie zawieraja petli i obslugi bledow - tylko wolaja te funkcje.

Uzywane w: views/observed_view.py, views/scanner_view.py
"""

import time

import pandas as pd
import streamlit as st

from services.analysis_service import analizuj
from services.scanner_service import skanuj_okazje, pobierz_wszystkie_tickery

# Przerwa miedzy zapytaniami - chroni przed limitami Yahoo Finance
PAUZA_ANALIZA = 0.3
PAUZA_SKANER = 0.2


def uruchom_analize_obserwowanych(spolki, universe_moje=None):
    """
    Analizuje wszystkie obserwowane spolki (pelna analiza + scoring).

    :param spolki: slownik {ticker: nazwa}
    :param universe_moje: slownik grupy "MOJE" (do oznaczenia rynku)
    :return: (DataFrame lub None, lista tickerow z bledem)
    """
    total = len(spolki)
    if total == 0:
        return None, []

    progress = st.progress(0)
    status = st.empty()

    wyniki, bledy = [], []

    for i, (ticker, nazwa) in enumerate(spolki.items()):
        status.text(f"Analizuje {i + 1}/{total}: {nazwa} ({ticker})")
        progress.progress((i + 1) / total)

        wynik = analizuj(ticker, nazwa, universe_moje=universe_moje)
        if wynik:
            wyniki.append(wynik)
        else:
            bledy.append(ticker)

        time.sleep(PAUZA_ANALIZA)

    progress.empty()
    status.empty()

    if not wyniki:
        return None, bledy

    df = pd.DataFrame(wyniki).sort_values("Score", ascending=False).reset_index(drop=True)
    return df, bledy


def uruchom_skaner(universe_dict):
    """
    Skanuje cale uniwersum okazji (szybka analiza).

    :param universe_dict: SCANNER_UNIVERSE_QUICK lub SCANNER_UNIVERSE_FULL
    :return: (DataFrame lub None, liczba nieudanych tickerow)
    """
    tickery = pobierz_wszystkie_tickery(universe_dict)
    total = len(tickery)
    if total == 0:
        return None, 0

    progress = st.progress(0)
    status = st.empty()

    wyniki, bledy = [], 0

    for i, ticker in enumerate(tickery):
        status.text(f"Skanuje {i + 1}/{total}: {ticker}")
        progress.progress((i + 1) / total)

        wynik = skanuj_okazje(ticker)
        if wynik:
            wyniki.append(wynik)
        else:
            bledy += 1

        time.sleep(PAUZA_SKANER)

    progress.empty()
    status.empty()

    if not wyniki:
        return None, bledy

    return pd.DataFrame(wyniki), bledy


def analizuj_liste(tickery_z_nazwami):
    """
    Analizuje wskazana liste spolek (np. sam koszyk) bez paska postepu.

    :param tickery_z_nazwami: lista par (ticker, nazwa)
    :return: DataFrame lub None
    """
    wyniki = []
    for ticker, nazwa in tickery_z_nazwami:
        wynik = analizuj(ticker, nazwa)
        if wynik:
            wyniki.append(wynik)
        time.sleep(PAUZA_ANALIZA)

    if not wyniki:
        return None
    return pd.DataFrame(wyniki).sort_values("Score", ascending=False).reset_index(drop=True)
