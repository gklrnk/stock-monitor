import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import time
warnings.filterwarnings("ignore")

# ==================== KONFIGURACJA STRONY ====================
st.set_page_config(
    page_title="Stock Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STYL CSS ====================
st.markdown("""
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
        height: 3rem;
        font-weight: bold;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1e3c72;
    }
    .opportunity-card {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 4px solid #1e3c72;
    }
</style>
""", unsafe_allow_html=True)

# ==================== UNIVERSUM WŁASNE (obserwowane) ====================
UNIVERSE_DEFAULT = {
    "GPW": {
        "PKO.WA": "PKO BP", "PEO.WA": "Pekao SA", "SAN.WA": "Santander Bank Polska",
        "MBK.WA": "mBank", "ALR.WA": "Alior Bank", "BHW.WA": "Bank Handlowy",
        "PZU.WA": "PZU", "XTB.WA": "XTB", "VOT.WA": "Votum", "GPW.WA": "GPW SA",
        "DNP.WA": "Dino Polska", "LPP.WA": "LPP", "ALE.WA": "Allegro",
        "EUR.WA": "Eurocash", "PCO.WA": "Pepco Group", "EAT.WA": "AmRest",
        "KGH.WA": "KGHM", "PKN.WA": "Orlen", "JSW.WA": "JSW",
        "KTY.WA": "Grupa Kety", "BDX.WA": "Budimex", "COG.WA": "Cognor",
        "ATC.WA": "Arctic Paper", "CDR.WA": "CD Projekt", "11B.WA": "11 bit studios",
        "ACP.WA": "Asseco Poland", "TXT.WA": "Text LiveChat", "CRI.WA": "Creotech",
        "LBW.WA": "Lubawa", "SNT.WA": "Synektik", "NEU.WA": "Neuca",
        "SLV.WA": "Selvita", "RVU.WA": "Ryvu Therapeutics", "DOM.WA": "Dom Development",
        "1AT.WA": "Atal", "DVL.WA": "Develia", "CAR.WA": "Inter Cars",
        "APR.WA": "Auto Partner", "BFT.WA": "Benefit Systems",
    },
    "GLOBAL": {
        "NVDA": "NVIDIA", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
        "ASML": "ASML", "TSM": "TSMC", "AVGO": "Broadcom", "AMD": "AMD",
        "LMT": "Lockheed Martin", "RHM.DE": "Rheinmetall", "BA.L": "BAE Systems",
        "NOC": "Northrop Grumman", "MC.PA": "LVMH", "RMS.PA": "Hermes",
        "RACE": "Ferrari", "COST": "Costco", "PEP": "PepsiCo",
        "XOM": "ExxonMobil", "RIO": "Rio Tinto", "CCJ": "Cameco",
        "BHP": "BHP Group", "FCX": "Freeport-McMoRan", "LLY": "Eli Lilly",
        "NVO": "Novo Nordisk", "UNH": "UnitedHealth", "ISRG": "Intuitive Surgical",
        "TMO": "Thermo Fisher", "JPM": "JPMorgan Chase", "BRK-B": "Berkshire Hathaway",
        "V": "Visa", "MA": "Mastercard", "BLK": "BlackRock", "TSLA": "Tesla",
        "TM": "Toyota", "UBER": "Uber", "PLTR": "Palantir", "CRWD": "CrowdStrike",
        "WM": "Waste Management", "ABNB": "Airbnb",
    },
    "MOJE": {}
}

# ==================== UNIVERSUM SKANERA ====================
# Spółki do skanowania okazji (nie muszą być obserwowane)

SCANNER_UNIVERSE_QUICK = {
    "GPW": [
        "PKO.WA","PEO.WA","SAN.WA","MBK.WA","ALR.WA","BHW.WA","PZU.WA","XTB.WA","GPW.WA",
        "DNP.WA","LPP.WA","ALE.WA","EUR.WA","PCO.WA","EAT.WA","KGH.WA","PKN.WA","JSW.WA",
        "KTY.WA","BDX.WA","COG.WA","ATC.WA","CDR.WA","11B.WA","ACP.WA","TXT.WA","CRI.WA",
        "LBW.WA","SNT.WA","NEU.WA","SLV.WA","RVU.WA","DOM.WA","1AT.WA","DVL.WA","CAR.WA",
        "APR.WA","BFT.WA","VOT.WA","OPL.WA","TPE.WA","PGE.WA","ENA.WA","LTS.WA","CPS.WA",
        "CIE.WA","MRC.WA","FTE.WA","PLW.WA","TEN.WA","BOS.WA","MIL.WA","ING.WA","HDR.WA",
        "GNB.WA","VRC.WA","PEP.WA","GRN.WA","ATT.WA","AMB.WA",
    ],
    "USA": [
        "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V","MA","UNH",
        "XOM","JNJ","LLY","AVGO","WMT","PG","HD","CVX","ABBV","BAC","KO","PFE","PEP",
        "TMO","COST","MRK","CSCO","ADBE","MCD","ACN","NFLX","AMD","LIN","DHR","TXN","VZ",
        "WFC","NEE","BMY","PM","RTX","QCOM","HON","LOW","UPS","ORCL","IBM","INTC","T",
        "GS","BLK","AXP","CAT","BA","DIS","GE","MMM","F","GM",
    ],
    "EUROPA": [
        "ASML","MC.PA","RMS.PA","OR.PA","SAP.DE","SIE.DE","NOVN.SW","NESN.SW","ROG.SW",
        "AZN.L","SHEL.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","BATS.L","LSEG.L",
        "BA.L","RHM.DE","AIR.PA","SU.PA","BN.PA","DTE.DE","BMW.DE","MBG.DE","VOW3.DE",
        "ALV.DE","BAS.DE","BAYN.DE","IFX.DE","LIN.DE","MUV2.DE","SAN.PA","TTE.PA",
        "ENGI.PA","STLA.MI","ISP.MI","ENI.MI","G.MI","UCG.MI","INGA.AS","PHIA.AS",
        "PRX.AS","ADYEN.AS","HEIA.AS","ITX.MC","BBVA.MC","SAN.MC","IBE.MC","REP.MC",
    ]
}

SCANNER_UNIVERSE_FULL = {
    "GPW": SCANNER_UNIVERSE_QUICK["GPW"] + [
        "CCC.WA","MBR.WA","STP.WA","KRU.WA","DAT.WA","MAB.WA","VRG.WA","APT.WA",
        "PKP.WA","BIO.WA","MOL.WA","ECH.WA","ATR.WA","GTC.WA","BML.WA","ACG.WA",
        "SGN.WA","STL.WA","AWM.WA","BRS.WA","OND.WA","LWB.WA","RBW.WA","INK.WA",
        "PXM.WA","MCI.WA","MEX.WA","QMK.WA","MDI.WA","ATG.WA","ACT.WA","ORB.WA",
        "IMS.WA","DVR.WA","AST.WA","BIK.WA","CMR.WA","CRJ.WA","CTX.WA","DSC.WA",
        "DUW.WA","EAI.WA","ELB.WA","ENP.WA","EPR.WA","ERG.WA","EUC.WA","FMF.WA",
        "FOR.WA","GCN.WA","HDL.WA","IZO.WA","KFT.WA","KGN.WA","KOM.WA","LEN.WA",
        "MFO.WA","MLG.WA","MLS.WA","MON.WA","NET.WA","NWG.WA","OAT.WA","OTM.WA",
        "PBX.WA","PCE.WA","PCX.WA","PJP.WA","PLD.WA","POZ.WA","QRS.WA","RFK.WA",
        "SEK.WA","SFG.WA","SNK.WA","SON.WA","STF.WA","TIM.WA","TRN.WA","UNI.WA",
    ],
    "USA": SCANNER_UNIVERSE_QUICK["USA"] + [
        "CRM","INTU","AMGN","AMAT","MDLZ","GILD","ADI","ISRG","BKNG","SBUX","VRTX",
        "MU","ADP","PLD","REGN","LRCX","SYK","TJX","MO","CI","BSX","ETN","SO","ZTS",
        "ITW","MMC","SLB","EOG","CB","APD","EQIX","NOC","AON","BDX","CME","ICE","FDX",
        "TGT","SHW","DUK","WM","ATVI","MAR","EMR","PNC","CSX","MPC","SNPS","PLD",
        "PANW","CRWD","NOW","MRVL","FTNT","SNOW","ZM","SQ","SHOP","PYPL","ROKU","UBER",
        "ABNB","DASH","COIN","LCID","RIVN","F","GM","LYFT","TWLO","DDOG",
    ],
    "EUROPA": SCANNER_UNIVERSE_QUICK["EUROPA"] + [
        "VNA.DE","DHL.DE","DBK.DE","CBK.DE","LHA.DE","RWE.DE","MRK.DE","HEN3.DE","BEI.DE",
        "SHL.DE","EOAN.DE","1COV.DE","AFX.DE","FRE.DE","MTX.DE","SY1.DE","VOD.L","LLOY.L",
        "BARC.L","NWG.L","STAN.L","PRU.L","AV.L","LGEN.L","TSCO.L","SBRY.L","MKS.L",
        "NG.L","SSE.L","CNA.L","BT-A.L","EZJ.L","IAG.L","RR.L","BAB.L","EDF.PA","VIV.PA",
        "SGO.PA","CAP.PA","ORA.PA","STM.PA","DSY.PA","ML.PA","EL.PA","KER.PA","ACA.PA",
        "GLE.PA","BNP.PA","AI.PA","MT.AS","AKZA.AS","WKL.AS","ASM.AS","BESI.AS","GLPG.AS",
    ]
}

# ==================== SESSION STATE ====================
if "UNIVERSE" not in st.session_state:
    st.session_state.UNIVERSE = UNIVERSE_DEFAULT.copy()
if "df" not in st.session_state:
    st.session_state.df = None
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None
if "scanner_df" not in st.session_state:
    st.session_state.scanner_df = None
if "scanner_last" not in st.session_state:
    st.session_state.scanner_last = None
if "news_cache" not in st.session_state:
    st.session_state.news_cache = {}

def get_all_tickers():
    all_t = {}
    for group in st.session_state.UNIVERSE.values():
        all_t.update(group)
    return all_t

def dodaj_do_obserwowanych(ticker, nazwa):
    """Dodaje spółkę do obserwowanych z Modułu 1 Skanera"""
    if ticker in get_all_tickers():
        return False, "Już jest na liście"
    st.session_state.UNIVERSE["MOJE"][ticker] = nazwa
    return True, "Dodano!"

# ==================== FUNKCJE ANALIZY GŁÓWNEJ ====================
def licz_rsi(close, okres=14):
    try:
        delta = close.diff()
        zysk = delta.where(delta > 0, 0.0)
        strata = -delta.where(delta < 0, 0.0)
        avg_z = zysk.rolling(window=okres).mean()
        avg_s = strata.rolling(window=okres).mean()
        rs = avg_z / avg_s
        rsi = 100 - (100 / (1 + rs))
        w = rsi.dropna()
        if len(w) > 0:
            return round(float(w.iloc[-1]), 1)
    except:
        pass
    return None

def licz_sma(close, okres):
    try:
        if len(close) >= okres:
            w = close.rolling(window=okres).mean().dropna()
            if len(w) > 0:
                return round(float(w.iloc[-1]), 2)
    except:
        pass
    return None

def licz_macd(close):
    try:
        if len(close) < 35:
            return None
        e12 = close.ewm(span=12).mean()
        e26 = close.ewm(span=26).mean()
        ml = e12 - e26
        sl = ml.ewm(span=9).mean()
        return "BULL" if float(ml.iloc[-1]) > float(sl.iloc[-1]) else "BEAR"
    except:
        pass
    return None

def pobierz_liczbe(info, klucz):
    try:
        v = info.get(klucz)
        if v is not None and v != "N/A":
            return float(v)
    except:
        pass
    return None

def zmiana_ceny(close, dni):
    try:
        if len(close) >= dni:
            s = float(close.iloc[-dni])
            a = float(close.iloc[-1])
            if s > 0:
                return round(((a - s) / s) * 100, 2)
    except:
        pass
    return None

def analizuj(ticker, nazwa):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist is None or hist.empty or len(hist) < 20:
            return None
        close = hist["Close"].squeeze()
        if not isinstance(close, pd.Series):
            return None
        cena = float(close.iloc[-1])
        rsi = licz_rsi(close)
        sma50 = licz_sma(close, 50)
        sma200 = licz_sma(close, 200)
        macd = licz_macd(close)
        nad_sma200 = cena > sma200 if sma200 else None
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

        score, ms, powody = 0, 0, []

        if pe and pe > 0:
            ms += 10
            if pe < 10: score += 10; powody.append(f"P/E {pe}")
            elif pe < 15: score += 7
            elif pe < 25: score += 4
            elif pe > 40: score -= 3
        if roe is not None:
            ms += 10
            if roe > 20: score += 10; powody.append(f"ROE {roe}%")
            elif roe > 15: score += 7
            elif roe > 10: score += 4
            elif roe < 5: score -= 2
        if mgn is not None:
            ms += 8
            if mgn > 20: score += 8; powody.append(f"Marza {mgn}%")
            elif mgn > 10: score += 5
            elif mgn > 5: score += 2
            elif mgn < 0: score -= 3
        if rg is not None:
            ms += 8
            if rg > 20: score += 8; powody.append(f"Wzrost {rg}%")
            elif rg > 10: score += 5
            elif rg > 0: score += 2
            elif rg < -10: score -= 3
        if de is not None:
            ms += 6
            if de < 50: score += 6; powody.append("Niski dlug")
            elif de < 100: score += 3
            elif de > 200: score -= 3
        if div and div > 0:
            ms += 5
            if div > 5: score += 5; powody.append(f"Dyw {div}%")
            elif div > 3: score += 3
            elif div > 1: score += 1
        if rec:
            ms += 8
            m = {"strongBuy": 8, "strong_buy": 8, "buy": 6, "hold": 3, "sell": -2, "strongSell": -5, "strong_sell": -5}
            s = m.get(str(rec), 0)
            score += s
            if s >= 6: powody.append(f"Analitycy: {rec}")
        if target and cena > 0:
            ms += 8
            up = ((target - cena) / cena) * 100
            if up > 30: score += 8; powody.append(f"Potencjal +{round(up)}%")
            elif up > 15: score += 5
            elif up > 0: score += 2
            elif up < -15: score -= 4
        if rsi is not None:
            ms += 8
            if rsi < 30: score += 8; powody.append(f"RSI wyprz. ({rsi})")
            elif rsi < 40: score += 5
            elif 40 <= rsi <= 60: score += 3
            elif rsi > 70: score -= 2; powody.append(f"RSI wykup. ({rsi})")
        if macd:
            ms += 6
            if macd == "BULL": score += 6; powody.append("MACD BULL")
            else: score -= 1
        if nad_sma200 is not None:
            ms += 6
            if nad_sma200: score += 6; powody.append("Nad SMA200")
            else: score -= 1

        zm1m = zmiana_ceny(close, 21)
        zm3m = zmiana_ceny(close, 63)
        if zm1m is not None:
            ms += 5
            if zm1m > 5: score += 5
            elif zm1m > 0: score += 2
        if zm3m is not None:
            ms += 5
            if zm3m > 15: score += 5
            elif zm3m > 5: score += 3

        pct = round((score / ms * 100), 1) if ms > 0 else 0

        if pct >= 70: sygnal = "🟢 KUPUJ"
        elif pct >= 55: sygnal = "🔵 OBSERWUJ"
        elif pct >= 40: sygnal = "⚪ TRZYMAJ"
        elif pct >= 25: sygnal = "🟡 OSTROZNIE"
        else: sygnal = "🔴 UNIKAJ"

        rynek = "GPW" if ticker.endswith(".WA") else "GLOBAL"
        if ticker in st.session_state.UNIVERSE.get("MOJE", {}):
            rynek = "⭐ MOJE"

        return {
            "Ticker": ticker, "Nazwa": nazwa, "Rynek": rynek, "Cena": round(cena, 2),
            "1T%": zmiana_ceny(close, 5), "1M%": zm1m, "3M%": zm3m,
            "6M%": zmiana_ceny(close, 126), "1R%": zmiana_ceny(close, 252),
            "PE": pe, "PBV": pb, "ROE": roe, "Marza": mgn, "Dywidenda": div,
            "DlugKap": de, "WzrostPrzych": rg, "Beta": beta, "MCapMld": mcap,
            "RSI": rsi, "SMA50": sma50, "SMA200": sma200, "MACD": macd,
            "NadSMA200": nad_sma200, "SYGNAL": sygnal, "Score": pct,
            "Powody": " | ".join(powody[:5]), "RekAnalit": rec,
            "CelAnalit": target, "LiczbaAnal": n_an,
        }
    except:
        return None

# ==================== FUNKCJE SKANERA OKAZJI ====================
def skanuj_okazje(ticker):
    """Szybka analiza pod kątem okazji - lżejsza niż analizuj()"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist is None or hist.empty or len(hist) < 20:
            return None

        close = hist["Close"].squeeze()
        volume = hist["Volume"].squeeze()

        if not isinstance(close, pd.Series):
            return None

        cena = float(close.iloc[-1])

        # Zmiany ceny
        chg_1d = zmiana_ceny(close, 2)
        chg_1w = zmiana_ceny(close, 5)
        chg_1m = zmiana_ceny(close, 21)
        chg_3m = zmiana_ceny(close, 63)

        # Wolumen
        vol_today = float(volume.iloc[-1])
        vol_avg = float(volume.tail(30).mean())
        vol_ratio = round((vol_today / vol_avg * 100), 0) if vol_avg > 0 else 0

        # 52W high/low
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

        # Odległość od szczytu/dołka
        od_high = round(((cena - w52h) / w52h * 100), 1) if w52h else None
        od_low = round(((cena - w52l) / w52l * 100), 1) if w52l else None

        # Techniczne
        rsi = licz_rsi(close)
        sma200 = licz_sma(close, 200)
        macd = licz_macd(close)
        nad_sma = cena > sma200 if sma200 else None

        # Fundamenty
        roe = round(roe_r * 100, 1) if roe_r else None
        mcap = round(mcap_r / 1e9, 2) if mcap_r else None
        pe_r = round(pe, 1) if pe else None

        # Klasyfikacja rynku
        if ticker.endswith(".WA"):
            rynek = "GPW"
        elif "." in ticker:
            rynek = "EUROPA"
        else:
            rynek = "USA"

        return {
            "Ticker": ticker,
            "Nazwa": nazwa,
            "Rynek": rynek,
            "Cena": round(cena, 2),
            "1D%": chg_1d,
            "1T%": chg_1w,
            "1M%": chg_1m,
            "3M%": chg_3m,
            "Wolumen%": vol_ratio,
            "52W_High": w52h,
            "52W_Low": w52l,
            "Od_High%": od_high,
            "Od_Low%": od_low,
            "PE": pe_r,
            "ROE": roe,
            "MCap_mld": mcap,
            "RSI": rsi,
            "MACD": macd,
            "Nad_SMA200": nad_sma,
        }
    except:
        return None

def pobierz_newsy(ticker, limit=8):
    """Pobiera newsy dla spółki z Yahoo Finance"""
    if ticker in st.session_state.news_cache:
        cached = st.session_state.news_cache[ticker]
        if (datetime.now() - cached["time"]).seconds < 3600:
            return cached["news"]

    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news[:limit] if stock.news else []

        parsed = []
        for n in news_list:
            try:
                title = n.get("title", "Brak tytułu")
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
                    "date": date_str
                })
            except:
                continue

        st.session_state.news_cache[ticker] = {
            "news": parsed,
            "time": datetime.now()
        }
        return parsed
    except:
        return []

def pobierz_kalendarz(tickers, dni=7):
    """Pobiera nadchodzące wyniki finansowe"""
    calendar_events = []
    today = datetime.now().date()
    limit_date = today + timedelta(days=dni)

    for ticker in tickers[:30]:
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal is not None and not cal.empty if hasattr(cal, 'empty') else cal:
                try:
                    if isinstance(cal, dict):
                        earnings_date = cal.get("Earnings Date")
                        if earnings_date:
                            if isinstance(earnings_date, list) and len(earnings_date) > 0:
                                ed = earnings_date[0]
                            else:
                                ed = earnings_date
                            if hasattr(ed, 'date'):
                                ed_date = ed.date()
                            else:
                                ed_date = ed
                            if today <= ed_date <= limit_date:
                                info = stock.info
                                calendar_events.append({
                                    "Ticker": ticker,
                                    "Nazwa": info.get("shortName", ticker),
                                    "Data": str(ed_date),
                                    "Typ": "📊 Wyniki finansowe"
                                })
                except:
                    pass
        except:
            continue
    return calendar_events

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 📊 Stock Monitor")
    st.markdown("---")

    st.markdown("### 🎯 GŁÓWNE AKCJE")

    if st.button("🔍 Analiza obserwowanych", type="primary"):
        st.session_state.run_scan = True

    st.markdown("### 🔎 SKANER OKAZJI")

    if st.button("⚡ Szybki skan (200 spółek)"):
        st.session_state.run_scanner = "quick"

    if st.button("🔬 Pełny skan (450 spółek)"):
        st.session_state.run_scanner = "full"

    st.markdown("---")
    st.markdown("### ➕ Dodaj spółkę")

    with st.form("dodaj_form"):
        new_ticker = st.text_input("Ticker (np. AAPL, CCC.WA)", key="new_ticker")
        new_nazwa = st.text_input("Nazwa (opcjonalnie)", key="new_nazwa")
        submitted = st.form_submit_button("➕ Dodaj")

        if submitted and new_ticker:
            ticker = new_ticker.upper().strip()
            all_t = get_all_tickers()
            if ticker in all_t:
                st.warning(f"Już jest: {all_t[ticker]}")
            else:
                with st.spinner(f"Sprawdzam {ticker}..."):
                    try:
                        s = yf.Ticker(ticker)
                        h = s.history(period="5d")
                        if h.empty:
                            st.error(f"❌ Nie znaleziono {ticker}")
                        else:
                            nazwa = new_nazwa if new_nazwa else (s.info.get("shortName") or ticker)
                            st.session_state.UNIVERSE["MOJE"][ticker] = nazwa
                            st.success(f"✅ Dodano: {nazwa}")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Błąd: {e}")

    st.markdown("### 🗑️ Usuń spółkę")
    all_t = get_all_tickers()
    if all_t:
        to_remove = st.selectbox("Wybierz:", [""] + list(all_t.keys()),
                                  format_func=lambda x: f"{x} - {all_t.get(x, '')}" if x else "-- wybierz --")
        if st.button("🗑️ Usuń") and to_remove:
            for gn, g in st.session_state.UNIVERSE.items():
                if to_remove in g:
                    del g[to_remove]
                    st.success(f"Usunięto {to_remove}")
                    time.sleep(1)
                    st.rerun()

    st.markdown("---")
    all_t = get_all_tickers()
    st.info(f"📊 Obserwowanych: **{len(all_t)}** spółek")
    if st.session_state.last_scan:
        st.caption(f"📅 Ost. analiza: {st.session_state.last_scan}")
    if st.session_state.scanner_last:
        st.caption(f"🔎 Ost. skan okazji: {st.session_state.scanner_last}")

# ==================== GŁÓWNA ZAWARTOŚĆ ====================
st.markdown('<div class="main-title">📊 STOCK MONITOR</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Monitor + Skaner okazji | GPW + USA + Europa</p>", unsafe_allow_html=True)

# GŁÓWNE ZAKŁADKI
main_tab1, main_tab2, main_tab3 = st.tabs([
    "📊 Obserwowane spółki",
    "🔎 Skaner okazji",
    "📅 Kalendarz wydarzeń"
])

# ==================== ZAKŁADKA 1: OBSERWOWANE ====================
with main_tab1:
    # SKANOWANIE OBSERWOWANYCH
    if st.session_state.get("run_scan"):
        all_t = get_all_tickers()
        total = len(all_t)
        st.session_state.run_scan = False

        st.info(f"🔄 Analizuję {total} obserwowanych spółek...")
        progress = st.progress(0)
        status = st.empty()

        wyniki = []
        bledy = []

        for i, (ticker, nazwa) in enumerate(all_t.items()):
            status.text(f"Analizuję {i+1}/{total}: {nazwa}")
            progress.progress((i + 1) / total)
            w = analizuj(ticker, nazwa)
            if w:
                wyniki.append(w)
            else:
                bledy.append(ticker)
            time.sleep(0.3)

        progress.empty()
        status.empty()

        if wyniki:
            df = pd.DataFrame(wyniki)
            df = df.sort_values("Score", ascending=False).reset_index(drop=True)
            st.session_state.df = df
            st.session_state.last_scan = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success(f"✅ Zakończono! Przeanalizowano {len(wyniki)} spółek.")
            if bledy:
                st.warning(f"⚠️ Nie znaleziono: {', '.join(bledy)}")

    if st.session_state.df is not None:
        df = st.session_state.df

        st.markdown("### 📈 Podsumowanie")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🟢 Kupuj", len(df[df["SYGNAL"].str.contains("KUPUJ")]))
        c2.metric("🔵 Obserwuj", len(df[df["SYGNAL"].str.contains("OBSERWUJ")]))
        c3.metric("⚪ Trzymaj", len(df[df["SYGNAL"].str.contains("TRZYMAJ")]))
        c4.metric("🟡 Ostrożnie", len(df[df["SYGNAL"].str.contains("OSTROZNIE")]))
        c5.metric("🔴 Unikaj", len(df[df["SYGNAL"].str.contains("UNIKAJ")]))

        st.markdown("---")

        st.markdown("### 🔍 Filtry")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            rynki = ["Wszystkie"] + sorted(df["Rynek"].unique().tolist())
            f_rynek = st.selectbox("Rynek", rynki)
        with fc2:
            sygnaly_opts = ["Wszystkie"] + df["SYGNAL"].unique().tolist()
            f_sygnal = st.selectbox("Sygnał", sygnaly_opts)
        with fc3:
            min_score = st.slider("Min. Score %", 0, 100, 0)

        filtered = df.copy()
        if f_rynek != "Wszystkie":
            filtered = filtered[filtered["Rynek"] == f_rynek]
        if f_sygnal != "Wszystkie":
            filtered = filtered[filtered["SYGNAL"] == f_sygnal]
        filtered = filtered[filtered["Score"] >= min_score]

        sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs(
            ["🏆 TOP 15", "📋 Tabela", "📊 Wykresy", "🔍 Analiza spółki", "📥 Eksport"]
        )

        with sub_tab1:
            st.markdown("### 🏆 TOP 15 Rekomendacji")
            top = filtered.head(15)
            for i, r in top.iterrows():
                with st.expander(f"#{i+1} {r['SYGNAL']} | {r['Nazwa']} ({r['Ticker']}) | Score: {r['Score']}%"):
                    cc1, cc2, cc3, cc4 = st.columns(4)
                    cc1.metric("Cena", r["Cena"])
                    cc2.metric("1M %", f"{r['1M%']}%" if r['1M%'] else "-")
                    cc3.metric("P/E", r["PE"] if r["PE"] else "-")
                    cc4.metric("RSI", r["RSI"] if r["RSI"] else "-")
                    st.markdown(f"**Powody:** {r['Powody']}")
                    st.markdown(f"**Rynek:** {r['Rynek']} | **Analitycy:** {r['RekAnalit'] or 'brak'} | **Cel:** {r['CelAnalit'] or 'brak'}")

        with sub_tab2:
            st.markdown(f"### 📋 Cała tabela ({len(filtered)} spółek)")
            cols = ["Ticker", "Nazwa", "Rynek", "Cena", "1M%", "3M%", "PE", "ROE", "Dywidenda", "RSI", "MACD", "SYGNAL", "Score", "Powody"]
            st.dataframe(
                filtered[cols].style.background_gradient(subset=["Score"], cmap="RdYlGn").format(precision=1, na_rep="-"),
                use_container_width=True, height=600
            )

        with sub_tab3:
            st.markdown("### 📊 Wykresy")
            kolory = {"🟢 KUPUJ": "#00aa00", "🔵 OBSERWUJ": "#3399ff", "⚪ TRZYMAJ": "#999999",
                      "🟡 OSTROZNIE": "#ffaa00", "🔴 UNIKAJ": "#cc0000"}
            fig1 = px.bar(filtered.head(20), x="Ticker", y="Score", color="SYGNAL",
                          hover_data=["Nazwa", "Cena", "1M%", "PE"],
                          title="TOP 20 spółek wg Score", color_discrete_map=kolory, height=450)
            st.plotly_chart(fig1, use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                fig2 = px.scatter(filtered, x="1M%", y="Score", color="Rynek", size="Score",
                                  hover_name="Nazwa", title="Momentum vs Score", height=400)
                fig2.add_hline(y=55, line_dash="dash", line_color="green")
                fig2.add_hline(y=70, line_dash="dash", line_color="darkgreen")
                st.plotly_chart(fig2, use_container_width=True)
            with c2:
                counts = filtered["SYGNAL"].value_counts()
                fig3 = px.pie(names=counts.index, values=counts.values,
                              title="Rozkład sygnałów", color=counts.index,
                              color_discrete_map=kolory, height=400)
                st.plotly_chart(fig3, use_container_width=True)

        with sub_tab4:
            st.markdown("### 🔍 Głęboka analiza spółki")
            all_t = get_all_tickers()
            wybor = st.selectbox("Wybierz spółkę:", list(all_t.keys()),
                                 format_func=lambda x: f"{x} - {all_t.get(x, '')}")
            if wybor:
                with st.spinner("Pobieram dane..."):
                    stock = yf.Ticker(wybor)
                    hist = stock.history(period="2y")
                    info = stock.info
                    nazwa = all_t.get(wybor, wybor)
                if not hist.empty:
                    close = hist["Close"].squeeze()
                    rzad = df[df["Ticker"] == wybor]
                    if len(rzad) > 0:
                        r = rzad.iloc[0]
                        st.markdown(f"## {nazwa} ({wybor})")
                        cc1, cc2, cc3 = st.columns(3)
                        cc1.metric("Sygnał", r["SYGNAL"])
                        cc2.metric("Score", f"{r['Score']}%")
                        cc3.metric("Cena", r["Cena"])
                        st.markdown("---")
                        st.markdown("#### 💰 Zmiany ceny")
                        zc = st.columns(5)
                        zc[0].metric("1T", f"{r['1T%']}%" if r['1T%'] else "-")
                        zc[1].metric("1M", f"{r['1M%']}%" if r['1M%'] else "-")
                        zc[2].metric("3M", f"{r['3M%']}%" if r['3M%'] else "-")
                        zc[3].metric("6M", f"{r['6M%']}%" if r['6M%'] else "-")
                        zc[4].metric("1R", f"{r['1R%']}%" if r['1R%'] else "-")
                        st.markdown("#### 📊 Fundamenty")
                        f1, f2, f3, f4, f5 = st.columns(5)
                        f1.metric("P/E", r["PE"] if r["PE"] else "-")
                        f2.metric("P/BV", r["PBV"] if r["PBV"] else "-")
                        f3.metric("ROE %", r["ROE"] if r["ROE"] else "-")
                        f4.metric("Marża %", r["Marza"] if r["Marza"] else "-")
                        f5.metric("Dyw. %", r["Dywidenda"] if r["Dywidenda"] else "-")
                        st.markdown(f"**💡 Powody:** {r['Powody']}")

                    st.markdown("#### 📈 Wykres techniczny")
                    sma20 = close.rolling(20).mean()
                    sma50 = close.rolling(50).mean()
                    sma200 = close.rolling(200).mean()
                    e12 = close.ewm(span=12).mean()
                    e26 = close.ewm(span=26).mean()
                    macd_l = e12 - e26
                    signal_l = macd_l.ewm(span=9).mean()
                    macd_h = macd_l - signal_l
                    delta = close.diff()
                    zysk = delta.where(delta > 0, 0.0)
                    strata = -delta.where(delta < 0, 0.0)
                    avg_z = zysk.rolling(14).mean()
                    avg_s = strata.rolling(14).mean()
                    rs = avg_z / avg_s
                    rsi_s = 100 - (100 / (1 + rs))

                    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                                        row_heights=[0.45, 0.15, 0.20, 0.20],
                                        vertical_spacing=0.02,
                                        subplot_titles=[f"{nazwa} - Cena + SMA", "Wolumen", "RSI", "MACD"])
                    fig.add_trace(go.Candlestick(x=hist.index, open=hist["Open"], high=hist["High"],
                                                  low=hist["Low"], close=hist["Close"], name="Cena"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=sma20, name="SMA20", line=dict(color="blue", width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=sma50, name="SMA50", line=dict(color="orange", width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=sma200, name="SMA200", line=dict(color="red", width=2)), row=1, col=1)
                    target = info.get("targetMeanPrice")
                    if target:
                        fig.add_hline(y=float(target), line_dash="dash", line_color="purple",
                                      annotation_text=f"Target: {round(float(target),2)}", row=1, col=1)
                    kv = ["green" if float(c) >= float(o) else "red" for c, o in zip(hist["Close"], hist["Open"])]
                    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Vol", marker_color=kv), row=2, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=rsi_s, name="RSI", line=dict(color="purple")), row=3, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=macd_l, name="MACD", line=dict(color="blue")), row=4, col=1)
                    fig.add_trace(go.Scatter(x=hist.index, y=signal_l, name="Signal", line=dict(color="orange")), row=4, col=1)
                    km = ["green" if float(v) >= 0 else "red" for v in macd_h]
                    fig.add_trace(go.Bar(x=hist.index, y=macd_h, name="Hist", marker_color=km), row=4, col=1)
                    fig.update_layout(height=900, showlegend=False, xaxis_rangeslider_visible=False)
                    fig.update_yaxes(range=[0, 100], row=3, col=1)
                    st.plotly_chart(fig, use_container_width=True)

        with sub_tab5:
            st.markdown("### 📥 Eksport danych")
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📄 Pobierz CSV", csv, f"stock_monitor_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Analiza")
            st.download_button("📊 Pobierz Excel", buffer.getvalue(),
                              f"stock_monitor_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.info("👈 Kliknij **Analiza obserwowanych** w panelu bocznym aby rozpocząć.")

# ==================== ZAKŁADKA 2: SKANER OKAZJI ====================
with main_tab2:
    st.markdown("### 🔎 Skaner okazji rynkowych")
    st.markdown("*Znajdź spółki które NIE są jeszcze na Twojej liście obserwowanych*")

    if st.session_state.get("run_scanner"):
        tryb = st.session_state.run_scanner
        st.session_state.run_scanner = None

        if tryb == "quick":
            uni = SCANNER_UNIVERSE_QUICK
            st.info("⚡ Rozpoczynam SZYBKI skan (~200 spółek, ~7 min)...")
        else:
            uni = SCANNER_UNIVERSE_FULL
            st.info("🔬 Rozpoczynam PEŁNY skan (~450 spółek, ~15-20 min)...")

        all_scanner_tickers = []
        for group_tickers in uni.values():
            all_scanner_tickers.extend(group_tickers)

        all_scanner_tickers = list(set(all_scanner_tickers))
        total = len(all_scanner_tickers)

        progress = st.progress(0)
        status = st.empty()

        scanner_results = []
        for i, ticker in enumerate(all_scanner_tickers):
            status.text(f"Skanuję {i+1}/{total}: {ticker}")
            progress.progress((i + 1) / total)
            w = skanuj_okazje(ticker)
            if w:
                scanner_results.append(w)
            time.sleep(0.2)

        progress.empty()
        status.empty()

        if scanner_results:
            sdf = pd.DataFrame(scanner_results)
            st.session_state.scanner_df = sdf
            st.session_state.scanner_last = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.success(f"✅ Zeskanowano {len(scanner_results)} spółek!")

    if st.session_state.scanner_df is not None:
        sdf = st.session_state.scanner_df

        st.markdown(f"*Ostatni skan: {st.session_state.scanner_last} | Spółek: {len(sdf)}*")

        # FILTRY GLOBALNE SKANERA
        sf1, sf2 = st.columns(2)
        with sf1:
            rynki_s = ["Wszystkie"] + sorted(sdf["Rynek"].unique().tolist())
            f_rynek_s = st.selectbox("Filtruj rynek:", rynki_s, key="scanner_rynek")

        sdf_f = sdf.copy()
        if f_rynek_s != "Wszystkie":
            sdf_f = sdf_f[sdf_f["Rynek"] == f_rynek_s]

        # ZAKŁADKI SKANERA
        s_tab = st.tabs([
            "🚀 Wzrosty", "💥 Spadki", "📊 Wolumen",
            "🏆 52W High", "📉 52W Low", "💎 Tanie", "🔥 Momentum"
        ])

        def render_okazje(dane, kolumny_extra, tytul, sort_col, ascending=False):
            """Renderuje listę okazji z przyciskami"""
            st.markdown(f"### {tytul}")

            if len(dane) == 0:
                st.info("Brak spółek spełniających kryteria")
                return

            dane_sorted = dane.sort_values(sort_col, ascending=ascending).head(20)

            for idx, row in dane_sorted.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])

                    with col1:
                        st.markdown(f"**{row['Nazwa']}** ({row['Ticker']})")
                        st.caption(f"Rynek: {row['Rynek']} | Cena: {row['Cena']}")

                    with col2:
                        for kol_key, kol_label in kolumny_extra[:2]:
                            val = row[kol_key]
                            if val is not None and pd.notna(val):
                                if "%" in kol_label:
                                    color = "green" if float(val) > 0 else "red" if float(val) < 0 else "gray"
                                    st.markdown(f"<small>{kol_label}: <b style='color:{color}'>{val}%</b></small>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<small>{kol_label}: <b>{val}</b></small>", unsafe_allow_html=True)

                    with col3:
                        for kol_key, kol_label in kolumny_extra[2:4]:
                            val = row[kol_key]
                            if val is not None and pd.notna(val):
                                st.markdown(f"<small>{kol_label}: <b>{val}</b></small>", unsafe_allow_html=True)

                    with col4:
                        bcol1, bcol2 = st.columns(2)
                        with bcol1:
                            if st.button("📰 News", key=f"news_{row['Ticker']}_{idx}"):
                                st.session_state[f"show_news_{row['Ticker']}"] = True
                        with bcol2:
                            already = row['Ticker'] in get_all_tickers()
                            if already:
                                st.caption("✅ już obserwowane")
                            else:
                                if st.button("➕ Obserwuj", key=f"add_{row['Ticker']}_{idx}"):
                                    ok, msg = dodaj_do_obserwowanych(row['Ticker'], row['Nazwa'])
                                    if ok:
                                        st.success(msg)
                                        time.sleep(1)
                                        st.rerun()

                    # Wyświetl newsy jeśli kliknięto
                    if st.session_state.get(f"show_news_{row['Ticker']}"):
                        with st.expander(f"📰 Newsy dla {row['Nazwa']}", expanded=True):
                            with st.spinner("Pobieram newsy..."):
                                newsy = pobierz_newsy(row['Ticker'])
                            if newsy:
                                for n in newsy:
                                    st.markdown(f"**{n['date']}** | *{n['publisher']}*")
                                    st.markdown(f"[{n['title']}]({n['link']})")
                                    st.markdown("---")
                            else:
                                st.info("Brak dostępnych newsów")
                            if st.button("✖️ Zamknij", key=f"close_{row['Ticker']}_{idx}"):
                                st.session_state[f"show_news_{row['Ticker']}"] = False
                                st.rerun()

                    st.markdown("---")

        with s_tab[0]:  # WZROSTY
            interval = st.radio("Okres:", ["1 dzień", "1 tydzień", "1 miesiąc", "3 miesiące"], horizontal=True, key="wzrost_int")
            col_map = {"1 dzień": "1D%", "1 tydzień": "1T%", "1 miesiąc": "1M%", "3 miesiące": "3M%"}
            col = col_map[interval]
            dane = sdf_f[sdf_f[col].notna() & (sdf_f[col] > 0)].copy()
            render_okazje(dane, [
                (col, f"Zmiana {interval}"),
                ("Wolumen%", "Wol %"),
                ("RSI", "RSI"),
                ("MACD", "MACD")
            ], f"🚀 TOP wzrosty ({interval})", col, ascending=False)

        with s_tab[1]:  # SPADKI
            interval2 = st.radio("Okres:", ["1 dzień", "1 tydzień", "1 miesiąc", "3 miesiące"], horizontal=True, key="spadek_int")
            col_map = {"1 dzień": "1D%", "1 tydzień": "1T%", "1 miesiąc": "1M%", "3 miesiące": "3M%"}
            col = col_map[interval2]
            dane = sdf_f[sdf_f[col].notna() & (sdf_f[col] < 0)].copy()
            render_okazje(dane, [
                (col, f"Zmiana {interval2}"),
                ("Wolumen%", "Wol %"),
                ("Od_High%", "Od 52W High %"),
                ("RSI", "RSI")
            ], f"💥 TOP spadki ({interval2}) - potencjalne okazje", col, ascending=True)

        with s_tab[2]:  # WOLUMEN
            dane = sdf_f[sdf_f["Wolumen%"] > 200].copy()
            render_okazje(dane, [
                ("Wolumen%", "Wol %"),
                ("1D%", "Zmiana 1D"),
                ("1T%", "Zmiana 1T"),
                ("RSI", "RSI")
            ], "📊 Nietypowy wolumen (>200% średniej) - coś się dzieje!", "Wolumen%", ascending=False)

        with s_tab[3]:  # 52W HIGH
            dane = sdf_f[sdf_f["Od_High%"].notna() & (sdf_f["Od_High%"] > -2)].copy()
            render_okazje(dane, [
                ("Od_High%", "Od 52W High %"),
                ("1M%", "Zmiana 1M"),
                ("52W_High", "52W High"),
                ("RSI", "RSI")
            ], "🏆 Blisko 52-week HIGH - silny trend wzrostowy", "Od_High%", ascending=False)

        with s_tab[4]:  # 52W LOW
            dane = sdf_f[sdf_f["Od_Low%"].notna() & (sdf_f["Od_Low%"] < 5)].copy()
            render_okazje(dane, [
                ("Od_Low%", "Od 52W Low %"),
                ("1M%", "Zmiana 1M"),
                ("52W_Low", "52W Low"),
                ("RSI", "RSI")
            ], "📉 Blisko 52-week LOW - potencjalne okazje", "Od_Low%", ascending=True)

        with s_tab[5]:  # TANIE
            dane = sdf_f[
                sdf_f["PE"].notna() & (sdf_f["PE"] > 0) & (sdf_f["PE"] < 12) &
                sdf_f["ROE"].notna() & (sdf_f["ROE"] > 10)
            ].copy()
            render_okazje(dane, [
                ("PE", "P/E"),
                ("ROE", "ROE %"),
                ("1M%", "Zmiana 1M"),
                ("MCap_mld", "MCap mld")
            ], "💎 Tanie fundamentalnie (P/E<12, ROE>10%)", "PE", ascending=True)

        with s_tab[6]:  # MOMENTUM
            dane = sdf_f[
                sdf_f["RSI"].notna() & (sdf_f["RSI"] >= 45) & (sdf_f["RSI"] <= 65) &
                (sdf_f["MACD"] == "BULL") &
                (sdf_f["Nad_SMA200"] == True) &
                sdf_f["1M%"].notna() & (sdf_f["1M%"] > 0)
            ].copy()
            render_okazje(dane, [
                ("1M%", "Zmiana 1M"),
                ("RSI", "RSI"),
                ("MACD", "MACD"),
                ("Nad_SMA200", "Nad SMA200")
            ], "🔥 Silne momentum techniczne", "1M%", ascending=False)

    else:
        st.info("👈 Kliknij **Szybki skan** lub **Pełny skan** w panelu bocznym aby rozpocząć.")

        st.markdown("### 📚 Co znajdzie skaner?")
        st.markdown("""
        - 🚀 **Wzrosty** - spółki które najbardziej urosły (dzień/tydzień/miesiąc/kwartał)
        - 💥 **Spadki** - duże spadki mogą oznaczać okazje kupna
        - 📊 **Wolumen** - nietypowa aktywność sugeruje że coś się dzieje
        - 🏆 **52W High** - spółki blisko rocznych szczytów (silny trend)
        - 📉 **52W Low** - spółki blisko rocznych dołków (potencjalne okazje)
        - 💎 **Tanie** - niedowartościowane fundamentalnie (niski P/E + wysokie ROE)
        - 🔥 **Momentum** - silny trend techniczny (RSI + MACD + SMA200)
        """)

# ==================== ZAKŁADKA 3: KALENDARZ ====================
with main_tab3:
    st.markdown("### 📅 Kalendarz wydarzeń dla obserwowanych")

    if st.button("🔄 Sprawdź nadchodzące wydarzenia"):
        with st.spinner("Sprawdzam kalendarze wyników..."):
            all_t = get_all_tickers()
            tickers = list(all_t.keys())
            wydarzenia = pobierz_kalendarz(tickers, dni=14)

            if wydarzenia:
                st.success(f"Znaleziono {len(wydarzenia)} wydarzeń w najbliższych 14 dniach")
                for w in wydarzenia:
                    st.markdown(f"**{w['Data']}** | {w['Typ']} | {w['Nazwa']} ({w['Ticker']})")
            else:
                st.info("Brak zaplanowanych wydarzeń w najbliższych 14 dniach dla obserwowanych spółek")

    st.markdown("---")
    st.info("💡 Wyniki finansowe potrafią mocno ruszyć kursem - warto śledzić kiedy je publikują")

st.markdown("---")
st.caption("⚠️ To narzędzie służy celom edukacyjnym. Nie stanowi porady inwestycyjnej. Dane: Yahoo Finance (opóźnienie ~15 min).")
