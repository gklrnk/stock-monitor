"""
INDICATORS - Wskazniki techniczne

Funkcje matematyczne uzywane w calej aplikacji:
- RSI (Relative Strength Index)
- SMA (Simple Moving Average)
- MACD (Moving Average Convergence Divergence)
- zmiany procentowe
- odczyt danych z Yahoo Finance

Uzywane w: analysis_service.py, scanner_service.py
"""

import pandas as pd
import warnings
warnings.filterwarnings("ignore")


def licz_rsi(close, okres=14):
    """
    Oblicza RSI (Relative Strength Index) - wskaznik momentum.
    
    RSI < 30 = wyprzedanie (potencjalna okazja kupna)
    RSI > 70 = wykupienie (potencjalna korekta)
    RSI 40-60 = neutralne
    
    :param close: seria cen zamkniecia
    :param okres: liczba dni (domyslnie 14)
    :return: wartosc RSI lub None jesli brak danych
    """
    try:
        delta = close.diff()
        zysk = delta.where(delta > 0, 0.0)
        strata = -delta.where(delta < 0, 0.0)
        avg_zysk = zysk.rolling(window=okres).mean()
        avg_strata = strata.rolling(window=okres).mean()
        rs = avg_zysk / avg_strata
        rsi = 100 - (100 / (1 + rs))
        wynik = rsi.dropna()
        if len(wynik) > 0:
            return round(float(wynik.iloc[-1]), 1)
    except:
        pass
    return None


def licz_sma(close, okres):
    """
    Oblicza SMA (Simple Moving Average) - srednia kroczaca.
    
    SMA50, SMA200 - popularne poziomy trendu.
    Cena > SMA200 = trend wzrostowy
    Cena < SMA200 = trend spadkowy
    
    :param close: seria cen zamkniecia
    :param okres: liczba dni (np. 50, 200)
    :return: wartosc SMA lub None
    """
    try:
        if len(close) >= okres:
            wynik = close.rolling(window=okres).mean().dropna()
            if len(wynik) > 0:
                return round(float(wynik.iloc[-1]), 2)
    except:
        pass
    return None


def licz_macd(close):
    """
    Oblicza MACD (Moving Average Convergence Divergence).
    
    Zwraca sygnal:
    - "BULL" gdy MACD > Signal (wzrostowy)
    - "BEAR" gdy MACD < Signal (spadkowy)
    
    :param close: seria cen zamkniecia
    :return: "BULL", "BEAR" lub None
    """
    try:
        if len(close) < 35:
            return None
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9).mean()
        m = float(macd_line.iloc[-1])
        s = float(signal_line.iloc[-1])
        return "BULL" if m > s else "BEAR"
    except:
        pass
    return None


def pobierz_liczbe(info, klucz):
    """
    Bezpiecznie pobiera liczbe ze slownika Yahoo Finance.
    
    Yahoo czasem zwraca None, "N/A" lub string zamiast liczby.
    Ta funkcja zawsze zwraca float albo None.
    
    :param info: slownik z Yahoo Finance (stock.info)
    :param klucz: nazwa wskaznika np. "trailingPE"
    :return: wartosc jako float lub None
    """
    try:
        v = info.get(klucz)
        if v is not None and v != "N/A":
            return float(v)
    except:
        pass
    return None


def zmiana_ceny(close, dni):
    """
    Oblicza zmiane procentowa ceny wzgledem N dni temu.
    
    Przyklad: zmiana_ceny(close, 5) = zmiana w ciagu tygodnia
    
    :param close: seria cen zamkniecia
    :param dni: liczba dni wstecz (5=tydzien, 21=miesiac, 63=kwartal)
    :return: zmiana w procentach lub None
    """
    try:
        if len(close) >= dni:
            stara = float(close.iloc[-dni])
            aktualna = float(close.iloc[-1])
            if stara > 0:
                return round(((aktualna - stara) / stara) * 100, 2)
    except:
        pass
    return None
