"""
SCANNER SERVICE - Szybki skaner okazji rynkowych

Ten modul zawiera lekka wersje analizy zoptymalizowana pod
skanowanie duzej liczby spolek (200-300 naraz).

W przeciwienstwie do analysis_service.py:
- Pobiera tylko 6 miesiecy danych (nie rok)
- Pomija pelne scoring
- Skupia sie na: wolumen, 52W high/low, momentum

Zwracane dane pozwalaja na filtrowanie okazji:
- Wzrosty/spadki (1D, 1T, 1M, 3M)
- Nietypowy wolumen (>200% sredniej)
- Blisko rocznych szczytow/dolkow
- Tanie fundamentalnie (P/E < 12, ROE > 10%)
- Silne technicznie (RSI + MACD + SMA200)

Uzywana w: pages/scanner_page.py
"""

import yfinance as yf
import pandas as pd
from services.indicators import (
    licz_rsi, licz_sma, licz_macd,
    pobierz_liczbe, zmiana_ceny
)


def skanuj_okazje(ticker):
    """
    Wykonuje szybka analize spolki pod katem okazji rynkowych.
    
    :param ticker: symbol np. "NVDA", "CDR.WA"
    :return: slownik z danymi do filtrowania lub None
    
    Przyklad zwrotu:
        {
            "Ticker": "NVDA",
            "Nazwa": "NVIDIA",
            "Rynek": "USA",
            "Cena": 920.50,
            "1D%": 2.1,
            "1T%": 5.3,
            "1M%": 12.5,
            "Wolumen%": 250,        # 250% sredniej!
            "52W_High": 950.00,
            "Od_High%": -3.1,       # 3.1% od szczytu
            "RSI": 65,
            "MACD": "BULL",
            "Nad_SMA200": True,
            ...
        }
    """
    try:
        # Pobierz dane historyczne (6 miesiecy - wystarczy do wolumenu)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        
        if hist is None or hist.empty or len(hist) < 20:
            return None
        
        close = hist["Close"].squeeze()
        volume = hist["Volume"].squeeze()
        
        if not isinstance(close, pd.Series):
            return None
        
        cena = float(close.iloc[-1])
        
        # ========== ZMIANY CEN ==========
        chg_1d = zmiana_ceny(close, 2)
        chg_1w = zmiana_ceny(close, 5)
        chg_1m = zmiana_ceny(close, 21)
        chg_3m = zmiana_ceny(close, 63)
        
        # ========== ANALIZA WOLUMENU ==========
        vol_today = float(volume.iloc[-1])
        vol_avg = float(volume.tail(30).mean())
        vol_ratio = round((vol_today / vol_avg * 100), 0) if vol_avg > 0 else 0
        
        # ========== DANE Z YAHOO INFO ==========
        try:
            info = stock.info
            w52h = pobierz_liczbe(info, "fiftyTwoWeekHigh")
            w52l = pobierz_liczbe(info, "fiftyTwoWeekLow")
            pe = pobierz_liczbe(info, "trailingPE")
            roe_r = pobierz_liczbe(info, "returnOnEquity")
            mcap_r = pobierz_liczbe(info, "marketCap")
            nazwa = info.get("shortName") or info.get("longName") or ticker
        except:
            w52h = w52l = pe = roe_r = mcap_r = None
            nazwa = ticker
        
        # ========== ODLEGLOSC OD 52W HIGH/LOW ==========
        od_high = round(((cena - w52h) / w52h * 100), 1) if w52h else None
        od_low = round(((cena - w52l) / w52l * 100), 1) if w52l else None
        
        # ========== WSKAZNIKI TECHNICZNE ==========
        rsi = licz_rsi(close)
        sma200 = licz_sma(close, 200)
        macd = licz_macd(close)
        nad_sma = cena > sma200 if sma200 else None
        
        # ========== FUNDAMENTY (uproszczone) ==========
        roe = round(roe_r * 100, 1) if roe_r else None
        mcap = round(mcap_r / 1e9, 2) if mcap_r else None
        pe_r = round(pe, 1) if pe else None
        
        # ========== KLASYFIKACJA RYNKU ==========
        if ticker.endswith(".WA"):
            rynek = "GPW"
        elif "." in ticker:
            rynek = "EUROPA"
        else:
            rynek = "USA"
        
        # ========== ZWROC WYNIK ==========
        return {
            "Ticker": ticker,
            "Nazwa": nazwa,
            "Rynek": rynek,
            "Cena": round(cena, 2),
            
            # Zmiany cen
            "1D%": chg_1d,
            "1T%": chg_1w,
            "1M%": chg_1m,
            "3M%": chg_3m,
            
            # Wolumen
            "Wolumen%": vol_ratio,
            
            # 52-week high/low
            "52W_High": w52h,
            "52W_Low": w52l,
            "Od_High%": od_high,
            "Od_Low%": od_low,
            
            # Fundamenty (podstawy)
            "PE": pe_r,
            "ROE": roe,
            "MCap_mld": mcap,
            
            # Techniczne
            "RSI": rsi,
            "MACD": macd,
            "Nad_SMA200": nad_sma,
        }
        
    except Exception as e:
        # Cichy blad - skaner nie moze sie zatrzymac na jednej spolce
        return None


def pobierz_wszystkie_tickery(universe_dict):
    """
    Wyplaszcza slownik uniwersum (GPW/USA/EUROPA) do jednej listy.
    
    :param universe_dict: np. SCANNER_UNIVERSE_QUICK lub _FULL
    :return: unikalna lista tickerow
    
    Przyklad:
        Wejscie:
            {"GPW": ["PKO.WA"], "USA": ["NVDA"], "EUROPA": ["ASML"]}
        Wyjscie:
            ["PKO.WA", "NVDA", "ASML"]
    """
    wszystkie = []
    for grupa_tickers in universe_dict.values():
        wszystkie.extend(grupa_tickers)
    return list(set(wszystkie))  # unikalne, bez duplikatow
