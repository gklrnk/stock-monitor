"""
ANALYSIS SERVICE - Glowna analiza fundamentalno-techniczna

Ten modul wykonuje pelna analize spolki i zwraca:
- Wszystkie kluczowe wskazniki (P/E, ROE, Marza, itd.)
- Wskazniki techniczne (RSI, MACD, SMA)
- Rekomendacje analitykow z Yahoo Finance
- SCORING 0-100% (system punktowy)
- SYGNAL: KUPUJ / OBSERWUJ / TRZYMAJ / OSTROZNIE / UNIKAJ

Uzywana w: pages/observed_page.py
"""

import yfinance as yf
import pandas as pd
from services.indicators import (
    licz_rsi, licz_sma, licz_macd,
    pobierz_liczbe, zmiana_ceny
)


def analizuj(ticker, nazwa, universe_moje=None):
    """
    Wykonuje pelna analize spolki.
    
    :param ticker: symbol np. "NVDA", "CDR.WA"
    :param nazwa: pelna nazwa np. "NVIDIA", "CD Projekt"
    :param universe_moje: slownik "MOJE" z session_state (do oznaczenia rynku)
    :return: slownik z pelna analiza lub None jesli blad
    
    Przyklad zwrotu:
        {
            "Ticker": "NVDA",
            "Nazwa": "NVIDIA",
            "Rynek": "GLOBAL",
            "Cena": 920.50,
            "1M%": 12.5,
            "PE": 45.2,
            "ROE": 55.0,
            "SYGNAL": "🟢 KUPUJ",
            "Score": 82.5,
            "Powody": "ROE 55% | Marza 32% | ...",
            ...
        }
    """
    try:
        # Pobierz dane historyczne (1 rok)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        
        if hist is None or hist.empty or len(hist) < 20:
            return None
        
        close = hist["Close"].squeeze()
        if not isinstance(close, pd.Series):
            return None
        
        cena = float(close.iloc[-1])
        
        # ========== WSKAZNIKI TECHNICZNE ==========
        rsi = licz_rsi(close)
        sma50 = licz_sma(close, 50)
        sma200 = licz_sma(close, 200)
        macd = licz_macd(close)
        nad_sma200 = cena > sma200 if sma200 else None
        
        # ========== DANE FUNDAMENTALNE ==========
        info = stock.info
        
        pe = pobierz_liczbe(info, "trailingPE")
        pb = pobierz_liczbe(info, "priceToBook")
        roe_r = pobierz_liczbe(info, "returnOnEquity")
        mgn_r = pobierz_liczbe(info, "profitMargins")
        div_r = pobierz_liczbe(info, "dividendYield")
        de = pobierz_liczbe(info, "debtToEquity")
        rg_r = pobierz_liczbe(info, "revenueGrowth")
        target = pobierz_liczbe(info, "targetMeanPrice")
        beta = pobierz_liczbe(info, "beta")
        mcap_r = pobierz_liczbe(info, "marketCap")
        rec = info.get("recommendationKey")
        n_an = info.get("numberOfAnalystOpinions")
        
        # Konwersja na procenty (Yahoo daje ulamki dziesietne)
        roe = round(roe_r * 100, 1) if roe_r else None
        mgn = round(mgn_r * 100, 1) if mgn_r else None
        div = round(div_r * 100, 2) if div_r else None
        rg = round(rg_r * 100, 1) if rg_r else None
        mcap = round(mcap_r / 1e9, 2) if mcap_r else None
        pe = round(pe, 1) if pe else None
        pb = round(pb, 2) if pb else None
        de = round(de, 0) if de else None
        beta = round(beta, 2) if beta else None
        target = round(target, 2) if target else None
        
        # ========== SYSTEM SCORINGU ==========
        score = 0
        max_score = 0
        powody = []
        
        # P/E (wycena)
        if pe and pe > 0:
            max_score += 10
            if pe < 10:
                score += 10
                powody.append(f"P/E {pe}")
            elif pe < 15:
                score += 7
            elif pe < 25:
                score += 4
            elif pe > 40:
                score -= 3
        
        # ROE (rentownosc kapitalu)
        if roe is not None:
            max_score += 10
            if roe > 20:
                score += 10
                powody.append(f"ROE {roe}%")
            elif roe > 15:
                score += 7
            elif roe > 10:
                score += 4
            elif roe < 5:
                score -= 2
        
        # Marza netto
        if mgn is not None:
            max_score += 8
            if mgn > 20:
                score += 8
                powody.append(f"Marza {mgn}%")
            elif mgn > 10:
                score += 5
            elif mgn > 5:
                score += 2
            elif mgn < 0:
                score -= 3
        
        # Wzrost przychodow
        if rg is not None:
            max_score += 8
            if rg > 20:
                score += 8
                powody.append(f"Wzrost {rg}%")
            elif rg > 10:
                score += 5
            elif rg > 0:
                score += 2
            elif rg < -10:
                score -= 3
        
        # Zadluzenie
        if de is not None:
            max_score += 6
            if de < 50:
                score += 6
                powody.append("Niski dlug")
            elif de < 100:
                score += 3
            elif de > 200:
                score -= 3
        
        # Dywidenda
        if div and div > 0:
            max_score += 5
            if div > 5:
                score += 5
                powody.append(f"Dyw {div}%")
            elif div > 3:
                score += 3
            elif div > 1:
                score += 1
        
        # Rekomendacje analitykow
        if rec:
            max_score += 8
            mapa = {
                "strongBuy": 8, "strong_buy": 8,
                "buy": 6,
                "hold": 3,
                "sell": -2,
                "strongSell": -5, "strong_sell": -5
            }
            s = mapa.get(str(rec), 0)
            score += s
            if s >= 6:
                powody.append(f"Analitycy: {rec}")
        
        # Potencjal wzrostu do target price
        if target and cena > 0:
            max_score += 8
            upside = ((target - cena) / cena) * 100
            if upside > 30:
                score += 8
                powody.append(f"Potencjal +{round(upside)}%")
            elif upside > 15:
                score += 5
            elif upside > 0:
                score += 2
            elif upside < -15:
                score -= 4
        
        # RSI (momentum)
        if rsi is not None:
            max_score += 8
            if rsi < 30:
                score += 8
                powody.append(f"RSI wyprz. ({rsi})")
            elif rsi < 40:
                score += 5
            elif 40 <= rsi <= 60:
                score += 3
            elif rsi > 70:
                score -= 2
                powody.append(f"RSI wykup. ({rsi})")
        
        # MACD (trend)
        if macd:
            max_score += 6
            if macd == "BULL":
                score += 6
                powody.append("MACD BULL")
            else:
                score -= 1
        
        # Trend dlugoterminowy (SMA200)
        if nad_sma200 is not None:
            max_score += 6
            if nad_sma200:
                score += 6
                powody.append("Nad SMA200")
            else:
                score -= 1
        
        # Momentum krotkoterminowy
        zm1m = zmiana_ceny(close, 21)
        zm3m = zmiana_ceny(close, 63)
        
        if zm1m is not None:
            max_score += 5
            if zm1m > 5:
                score += 5
            elif zm1m > 0:
                score += 2
        
        if zm3m is not None:
            max_score += 5
            if zm3m > 15:
                score += 5
            elif zm3m > 5:
                score += 3
        
        # ========== WYNIK KONCOWY ==========
        pct = round((score / max_score * 100), 1) if max_score > 0 else 0
        
        # Rekomendacja koncowa na podstawie score
        if pct >= 70:
            sygnal = "🟢 KUPUJ"
        elif pct >= 55:
            sygnal = "🔵 OBSERWUJ"
        elif pct >= 40:
            sygnal = "⚪ TRZYMAJ"
        elif pct >= 25:
            sygnal = "🟡 OSTROZNIE"
        else:
            sygnal = "🔴 UNIKAJ"
        
        # Klasyfikacja rynku
        rynek = "GPW" if ticker.endswith(".WA") else "GLOBAL"
        if universe_moje and ticker in universe_moje:
            rynek = "⭐ MOJE"
        
        # ========== ZWROC PELNY WYNIK ==========
        return {
            "Ticker": ticker,
            "Nazwa": nazwa,
            "Rynek": rynek,
            "Cena": round(cena, 2),
            
            # Zmiany cen
            "1T%": zmiana_ceny(close, 5),
            "1M%": zm1m,
            "3M%": zm3m,
            "6M%": zmiana_ceny(close, 126),
            "1R%": zmiana_ceny(close, 252),
            
            # Fundamenty
            "PE": pe,
            "PBV": pb,
            "ROE": roe,
            "Marza": mgn,
            "Dywidenda": div,
            "DlugKap": de,
            "WzrostPrzych": rg,
            "Beta": beta,
            "MCapMld": mcap,
            
            # Techniczne
            "RSI": rsi,
            "SMA50": sma50,
            "SMA200": sma200,
            "MACD": macd,
            "NadSMA200": nad_sma200,
            
            # Werdykt
            "SYGNAL": sygnal,
            "Score": pct,
            "Powody": " | ".join(powody[:5]),
            
            # Analitycy
            "RekAnalit": rec,
            "CelAnalit": target,
            "LiczbaAnal": n_an,
        }
        
    except Exception as e:
        # Cichy blad - aplikacja nie moze sie zawiesic dla jednej spolki
        return None
