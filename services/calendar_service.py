"""
CALENDAR SERVICE - Kalendarz wydarzen finansowych

Ten modul pobiera nadchodzace wydarzenia dla obserwowanych spolek:
- Wyniki finansowe (earnings dates)
- Dywidendy (daty wyplat)
- Splity akcji

Dane z Yahoo Finance (bezplatnie, opoznienie ~15 min).

Uwaga: Yahoo nie zawsze ma pelne dane dla malych spolek GPW.
Dla duzych spolek USA/Europa dane sa zwykle kompletne.

Uzywane w: pages/calendar_page.py
"""

import yfinance as yf
from datetime import datetime, timedelta


def pobierz_kalendarz_wynikow(tickery, dni=14):
    """
    Pobiera nadchodzace wyniki finansowe dla listy spolek.
    
    :param tickery: lista tickerow np. ["NVDA", "CDR.WA", "MSFT"]
    :param dni: horyzont czasowy (domyslnie 14 dni)
    :return: lista wydarzen posortowana chronologicznie
    
    Przyklad zwrotu:
        [
            {
                "Ticker": "NVDA",
                "Nazwa": "NVIDIA",
                "Data": "2026-08-15",
                "Typ": "📊 Wyniki finansowe",
                "Dni_do": 4
            },
            ...
        ]
    """
    wydarzenia = []
    today = datetime.now().date()
    limit_date = today + timedelta(days=dni)
    
    # Ograniczenie do 30 spolek zeby nie przeciazyc Yahoo
    for ticker in tickery[:30]:
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            
            if cal is None:
                continue
            
            try:
                # Yahoo zwraca kalendarz w roznych formatach
                if isinstance(cal, dict):
                    earnings_date = cal.get("Earnings Date")
                    
                    if earnings_date:
                        # Data moze byc lista lub pojedyncza wartoscia
                        if isinstance(earnings_date, list) and len(earnings_date) > 0:
                            ed = earnings_date[0]
                        else:
                            ed = earnings_date
                        
                        # Konwersja na date
                        if hasattr(ed, 'date'):
                            ed_date = ed.date()
                        else:
                            ed_date = ed
                        
                        # Sprawdz czy w zakresie
                        if today <= ed_date <= limit_date:
                            info = stock.info
                            dni_do = (ed_date - today).days
                            
                            wydarzenia.append({
                                "Ticker": ticker,
                                "Nazwa": info.get("shortName", ticker),
                                "Data": str(ed_date),
                                "Typ": "📊 Wyniki finansowe",
                                "Dni_do": dni_do
                            })
            except:
                # Pomin uszkodzony wpis, idz dalej
                pass
                
        except:
            # Pomin spolke z problemem, kontynuuj
            continue
    
    # Sortuj chronologicznie (najblizsze pierwsze)
    wydarzenia.sort(key=lambda x: x["Dni_do"])
    
    return wydarzenia


def pobierz_kalendarz_dywidend(tickery, dni=30):
    """
    Pobiera nadchodzace daty ex-dividend dla listy spolek.
    
    Ex-dividend date = ostatni dzien kiedy trzeba miec akcje
    zeby dostac dywidende.
    
    :param tickery: lista tickerow
    :param dni: horyzont czasowy (domyslnie 30 dni)
    :return: lista dywidend
    
    Przyklad zwrotu:
        [
            {
                "Ticker": "PZU.WA",
                "Nazwa": "PZU",
                "Data_ex": "2026-08-20",
                "Kwota": 4.50,
                "Waluta": "PLN",
                "Yield%": 5.2,
                "Dni_do": 9
            },
            ...
        ]
    """
    dywidendy = []
    today = datetime.now().date()
    limit_date = today + timedelta(days=dni)
    
    for ticker in tickery[:30]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Sprawdz ex-dividend date
            ex_date_ts = info.get("exDividendDate")
            
            if ex_date_ts:
                # Konwersja z timestamp
                ex_date = datetime.fromtimestamp(ex_date_ts).date()
                
                # Sprawdz czy w zakresie i w przyszlosci
                if today <= ex_date <= limit_date:
                    dni_do = (ex_date - today).days
                    kwota = info.get("dividendRate", 0)
                    yield_r = info.get("dividendYield", 0)
                    yield_pct = round(yield_r * 100, 2) if yield_r else 0
                    
                    # Waluta na podstawie rynku
                    if ticker.endswith(".WA"):
                        waluta = "PLN"
                    elif ticker.endswith(".L"):
                        waluta = "GBP"
                    elif "." in ticker and ticker.endswith((".DE", ".PA", ".AS", ".MI", ".MC")):
                        waluta = "EUR"
                    else:
                        waluta = "USD"
                    
                    dywidendy.append({
                        "Ticker": ticker,
                        "Nazwa": info.get("shortName", ticker),
                        "Data_ex": str(ex_date),
                        "Kwota": round(kwota, 2) if kwota else 0,
                        "Waluta": waluta,
                        "Yield%": yield_pct,
                        "Dni_do": dni_do
                    })
        except:
            continue
    
    # Sortuj chronologicznie
    dywidendy.sort(key=lambda x: x["Dni_do"])
    
    return dywidendy


def pobierz_pelny_kalendarz(tickery, dni=14):
    """
    Pobiera KOMPLETNY kalendarz - wyniki + dywidendy razem.
    
    Uzywane w zakladce "Kalendarz wydarzen" jako glowny widok.
    
    :param tickery: lista tickerow obserwowanych spolek
    :param dni: horyzont czasowy
    :return: slownik z podzialem na typy
    
    Przyklad zwrotu:
        {
            "wyniki": [...],
            "dywidendy": [...],
            "razem": 8,
            "najblizsze_dni": 2
        }
    """
    wyniki = pobierz_kalendarz_wynikow(tickery, dni)
    dywidendy = pobierz_kalendarz_dywidend(tickery, dni)
    
    # Znajdz najblizsze wydarzenie
    najblizsze = 999
    if wyniki:
        najblizsze = min(najblizsze, wyniki[0]["Dni_do"])
    if dywidendy:
        najblizsze = min(najblizsze, dywidendy[0]["Dni_do"])
    
    return {
        "wyniki": wyniki,
        "dywidendy": dywidendy,
        "razem": len(wyniki) + len(dywidendy),
        "najblizsze_dni": najblizsze if najblizsze < 999 else None
    }


def formatuj_dni_do(dni):
    """
    Formatuje liczbe dni na czytelny tekst.
    
    :param dni: liczba dni
    :return: string np. "dzisiaj", "jutro", "za 5 dni"
    """
    if dni == 0:
        return "🔴 DZISIAJ"
    elif dni == 1:
        return "🟠 jutro"
    elif dni <= 3:
        return f"🟡 za {dni} dni"
    elif dni <= 7:
        return f"🟢 za {dni} dni"
    else:
        return f"⚪ za {dni} dni"
