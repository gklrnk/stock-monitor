"""
NEWS SERVICE - Pobieranie i cache'owanie newsow

Ten modul obsluguje newsy spolek z Yahoo Finance.

Kluczowe cechy:
- Cache 1 godzine (nie pobiera tego samego 2 razy)
- Pobieranie tylko na zadanie (nie automatyczne)
- Bezpieczne obsluga bledow (zwroci pusta liste, nie wywali app)
- Formatowanie dat z timestamp na czytelne

Obsluguje DWA formaty odpowiedzi Yahoo:
- nowy (zagniezdzony w kluczu "content") - obecny yfinance
- stary (plaski, z providerPublishTime) - starsze wersje biblioteki

Uzywane w: components/stock_card.py, views/basket_view.py
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
        surowe = stock.news or []

        parsed = []
        for n in surowe[:limit]:
            wpis = _parsuj_news(n)
            if wpis:
                parsed.append(wpis)

        _zapisz_do_cache(ticker, parsed)
        return parsed

    except Exception:
        # Blad sieci / API - zwracamy pusta liste, aplikacja dziala dalej
        return []


def _parsuj_news(n):
    """
    Zamienia surowy wpis Yahoo na jednolity slownik.

    :return: {"title","publisher","link","date","timestamp"} lub None
    """
    try:
        # Nowy format: dane siedza w kluczu "content"
        c = n.get("content") if isinstance(n, dict) else None

        if isinstance(c, dict):
            title = c.get("title") or "Brak tytulu"
            publisher = (c.get("provider") or {}).get("displayName") or "Nieznany"
            link = (
                (c.get("clickThroughUrl") or {}).get("url")
                or (c.get("canonicalUrl") or {}).get("url")
                or "#"
            )
            data_txt = c.get("pubDate") or c.get("displayTime") or ""
            dt = _parsuj_date(data_txt)
        else:
            # Stary, plaski format
            title = n.get("title", "Brak tytulu")
            publisher = n.get("publisher", "Nieznany")
            link = n.get("link", "#")
            ts = n.get("providerPublishTime", 0)
            dt = datetime.fromtimestamp(ts) if ts else None

        return {
            "title": title,
            "publisher": publisher,
            "link": link,
            "date": dt.strftime("%Y-%m-%d %H:%M") if dt else "brak daty",
            "timestamp": dt.timestamp() if dt else 0,
        }
    except Exception:
        return None


def _parsuj_date(tekst):
    """Parsuje date ISO 8601 z Yahoo (np. '2026-08-14T21:29:00Z')."""
    if not tekst:
        return None
    try:
        return datetime.fromisoformat(str(tekst).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


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
