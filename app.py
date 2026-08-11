import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
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
</style>
""", unsafe_allow_html=True)

# ==================== UNIVERSUM SPÓŁEK ====================
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

# Session state
if "UNIVERSE" not in st.session_state:
    st.session_state.UNIVERSE = UNIVERSE_DEFAULT.copy()
if "df" not in st.session_state:
    st.session_state.df = None
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None

def get_all_tickers():
    all_t = {}
    for group in st.session_state.UNIVERSE.values():
        all_t.update(group)
    return all_t

# ==================== FUNKCJE ANALIZY ====================
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

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 📊 Stock Monitor")
    st.markdown("---")

    st.markdown("### ⚙️ Akcje")

    if st.button("🚀 URUCHOM SKANOWANIE", type="primary"):
        st.session_state.run_scan = True

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

    st.markdown("---")
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
        st.caption(f"Ostatni skan: {st.session_state.last_scan}")

# ==================== GŁÓWNA ZAWARTOŚĆ ====================
st.markdown('<div class="main-title">📊 STOCK MONITOR</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Monitor spółek GPW + rynki globalne | Analiza fundamentalna i techniczna</p>", unsafe_allow_html=True)

# SKANOWANIE
if st.session_state.get("run_scan"):
    all_t = get_all_tickers()
    total = len(all_t)
    st.session_state.run_scan = False

    st.info(f"🔄 Skanuję {total} spółek... To potrwa 3-5 minut. Czekaj cierpliwie!")
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
            st.warning(f"⚠️ Nie znaleziono danych: {', '.join(bledy)}")

# WYŚWIETLANIE WYNIKÓW
if st.session_state.df is not None:
    df = st.session_state.df

    # METRYKI
    st.markdown("### 📈 Podsumowanie")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🟢 Kupuj", len(df[df["SYGNAL"].str.contains("KUPUJ")]))
    c2.metric("🔵 Obserwuj", len(df[df["SYGNAL"].str.contains("OBSERWUJ")]))
    c3.metric("⚪ Trzymaj", len(df[df["SYGNAL"].str.contains("TRZYMAJ")]))
    c4.metric("🟡 Ostrożnie", len(df[df["SYGNAL"].str.contains("OSTROZNIE")]))
    c5.metric("🔴 Unikaj", len(df[df["SYGNAL"].str.contains("UNIKAJ")]))

    st.markdown("---")

    # FILTRY
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

    # ZAKŁADKI
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 TOP 15", "📋 Cała tabela", "📊 Wykresy", "🔍 Analiza spółki", "📥 Eksport"])

    with tab1:
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

    with tab2:
        st.markdown(f"### 📋 Cała tabela ({len(filtered)} spółek)")
        cols = ["Ticker", "Nazwa", "Rynek", "Cena", "1M%", "3M%", "PE", "ROE", "Dywidenda", "RSI", "MACD", "SYGNAL", "Score", "Powody"]
        st.dataframe(
            filtered[cols].style.background_gradient(subset=["Score"], cmap="RdYlGn").format(precision=1, na_rep="-"),
            use_container_width=True, height=600
        )

    with tab3:
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

    with tab4:
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
                cena = float(close.iloc[-1])

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

                    st.markdown("#### 📈 Techniczne")
                    t1, t2, t3, t4 = st.columns(4)
                    t1.metric("RSI", r["RSI"] if r["RSI"] else "-")
                    t2.metric("MACD", r["MACD"] if r["MACD"] else "-")
                    t3.metric("SMA 200", r["SMA200"] if r["SMA200"] else "-")
                    t4.metric("Trend", "↑ WZROST" if r["NadSMA200"] else "↓ SPADEK")

                    st.markdown(f"**💡 Powody rekomendacji:** {r['Powody']}")
                    st.markdown(f"**🏦 Analitycy:** {r['RekAnalit']} | **🎯 Cena docelowa:** {r['CelAnalit']} | **👥 Opinie:** {r['LiczbaAnal']}")

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

    with tab5:
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
    # Ekran startowy
    st.info("👈 Kliknij **URUCHOM SKANOWANIE** w panelu bocznym aby rozpocząć analizę.")
    st.markdown("### 📋 Aktualnie obserwowane spółki")
    all_t = get_all_tickers()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"#### 🇵🇱 GPW ({len(st.session_state.UNIVERSE['GPW'])})")
        for t, n in list(st.session_state.UNIVERSE["GPW"].items())[:15]:
            st.markdown(f"- **{t}** {n}")
        if len(st.session_state.UNIVERSE["GPW"]) > 15:
            st.caption(f"...i {len(st.session_state.UNIVERSE['GPW']) - 15} więcej")
    with c2:
        st.markdown(f"#### 🌍 Globalne ({len(st.session_state.UNIVERSE['GLOBAL'])})")
        for t, n in list(st.session_state.UNIVERSE["GLOBAL"].items())[:15]:
            st.markdown(f"- **{t}** {n}")
        if len(st.session_state.UNIVERSE["GLOBAL"]) > 15:
            st.caption(f"...i {len(st.session_state.UNIVERSE['GLOBAL']) - 15} więcej")
    with c3:
        st.markdown(f"#### ⭐ Moje ({len(st.session_state.UNIVERSE['MOJE'])})")
        if st.session_state.UNIVERSE["MOJE"]:
            for t, n in st.session_state.UNIVERSE["MOJE"].items():
                st.markdown(f"- **{t}** {n}")
        else:
            st.caption("Dodaj swoje w panelu bocznym →")

st.markdown("---")
st.caption("⚠️ To narzędzie służy celom edukacyjnym. Nie stanowi porady inwestycyjnej. Dane: Yahoo Finance (opóźnienie ~15 min).")
