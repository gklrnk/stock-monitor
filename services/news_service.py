"""
NEWS SERVICE - Pobieranie i cache'owanie newsow

Ten modul obsluguje newsy spolek z Yahoo Finance.

Kluczowe cechy:
- Cache 1 godzine (nie pobiera tego samego 2 razy)
- Pobieranie tylko na zadanie (nie automatyczne)
- Bezpieczne obsluga bledow (zwroci pusta liste, nie wywali app)
- Formatowanie dat z timestamp na czytelne

Uzywane w: pages/scanner_page.py, pages/basket_page.py
"""

import streamlit as st
import yfinance as yf
from datetime import datetime


def pobierz_newsy(ticker, limit=8):
    """
    Pobiera newsy dla spolki z Yahoo Finance z cache'owaniem.
    
    :param ticker: symbol np. "NVDA", "CDR.WA"
    :param limit: maksymalna liczba newsow (domyslnie 8)
    :return: lista slownikow z newsami
    
    Przyklad zwrotu:
        [
            {
                "title": "NVIDIA Reports Record Q3 Earnings",
                "publisher": "Reuters",
                "link": "https://...",
                "date": "2026-08-11 14:30"
            },
            ...
        ]
    """
    # Sprawdz cache (unikamy pobierania tego samego 2x)
    if _sprawdz_cache(ticker):
        return _pobierz_z_cache(ticker)
    
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news[:limit] if stock.news else []
        
        parsed = []
        for n in news_list:
            try:
                title = n.get("title", "Brak tytulu")
                publisher = n.get("publisher", "Nieznany")
                link = n.get("link", "#")
                timestamp = n.get("providerPublishTime", 0)
                
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                else:
                    date_str = "brak daty"
                
                parsed.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "date": date_str,
                    "timestamp": timestamp
                })
            except:
                # Pomin uszkodzony news i idz dalej
                continue
        
        # Zapisz do cache
        _zapisz_do_cache(ticker, parsed)
        
        return parsed
        
    except Exception as e:
        # Jesli blad - zwroc pusta liste, nie wywalaj aplikacji
        return []


def pobierz_newsy_dla_wielu(tickery, limit_na_spolke=5):
    """
    Pobiera newsy dla wielu spolek naraz (zbiorczy feed).
    
    Uzywane w koszyku analitycznym do pokazania wszystkich
    newsow dla wybranych spolek posortowanych chronologicznie.
    
    :param tickery: lista tickerow np. ["NVDA", "CDR.WA", "MSFT"]
    :param limit_na_spolke: ile newsow z kazdej spolki
    :return: polaczona lista newsow posortowana po dacie (najnowsze pierwsze)
    """
    wszystkie = []
    
    for ticker in tickery:
        newsy = pobierz_newsy(ticker, limit=limit_na_spolke)
        # Dodaj ticker do kazdego newsa (zeby wiedziec z ktorej spolki)
        for news in newsy:
            news["ticker"] = ticker
            wszystkie.append(news)
    
    # Sortuj po dacie (najnowsze pierwsze)
    wszystkie.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return wszystkie


def wyczysc_cache():
    """
    Czysci caly cache newsow.
    
    Uzywane gdy chcesz wymusic pobranie swiezych danych
    (np. przycisk "Odswiez newsy" w aplikacji).
    """
    if "news_cache" in st.session_state:
        st.session_state.news_cache = {}


# ========== FUNKCJE WEWNETRZNE (cache) ==========

def _sprawdz_cache(ticker):
    """Sprawdza czy w cache sa aktualne dane (mlodsze niz 1h)."""
    if "news_cache" not in st.session_state:
        return False
    
    if ticker not in st.session_state.news_cache:
        return False
    
    cached = st.session_state.news_cache[ticker]
    czas_od_cache = (datetime.now() - cached["time"]).seconds
    
    # Cache wazny przez 1 godzine (3600 sekund)
    return czas_od_cache < 3600


def _pobierz_z_cache(ticker):
    """Zwraca dane z cache."""
    return st.session_state.news_cache[ticker]["news"]


def _zapisz_do_cache(ticker, dane):
    """Zapisuje dane do cache z timestampem."""
    if "news_cache" not in st.session_state:
        st.session_state.news_cache = {}
    
    st.session_state.news_cache[ticker] = {
        "news": dane,
        "time": datetime.now()
    }
