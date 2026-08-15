"""
SCANNER VIEW - Zakladka "Skaner okazji"

Przeszukuje 200-300 spolek (GPW + USA + Europa) i pokazuje je
w 7 przekrojach: wzrosty, spadki, wolumen, 52W High, 52W Low,
tanie fundamentalnie, momentum.

Kazda karta ma przyciski: newsy, dodaj do obserwowanych, dodaj do koszyka.
"""

import streamlit as st

from components.stock_card import render_karta
from config.universe import SCANNER_UNIVERSE_QUICK, SCANNER_UNIVERSE_FULL
from services import export_service as exp
from services.runner_service import uruchom_skaner
from utils.session_state import oznacz_skan

OKRESY = {"1 dzien": "1D%", "1 tydzien": "1T%", "1 miesiac": "1M%", "3 miesiace": "3M%"}


def render():
    """Punkt wejscia zakladki."""
    st.markdown("### 🔎 Skaner okazji rynkowych")
    st.caption("Znajdz spolki, ktorych nie masz jeszcze na liscie obserwowanych.")

    _obsluz_uruchomienie()

    if st.session_state.scanner_df is None:
        st.info("👈 Kliknij **Szybki skan** lub **Pelny skan** w panelu bocznym.")
        _pomoc()
        return

    sdf = st.session_state.scanner_df
    st.caption(f"Ostatni skan: {st.session_state.scanner_last} | Spolek: {len(sdf)}")

    sdf_f = _filtr_rynku(sdf)
    zakladki = st.tabs([
        "🚀 Wzrosty", "💥 Spadki", "📊 Wolumen", "🏆 52W High",
        "📉 52W Low", "💎 Tanie", "🔥 Momentum", "📥 Eksport",
    ])

    with zakladki[0]:
        _wzrosty(sdf_f)
    with zakladki[1]:
        _spadki(sdf_f)
    with zakladki[2]:
        _wolumen(sdf_f)
    with zakladki[3]:
        _high52(sdf_f)
    with zakladki[4]:
        _low52(sdf_f)
    with zakladki[5]:
        _tanie(sdf_f)
    with zakladki[6]:
        _momentum(sdf_f)
    with zakladki[7]:
        _eksport(sdf)


def _obsluz_uruchomienie():
    """Uruchamia skan gdy w sidebarze wcisnieto przycisk."""
    tryb = st.session_state.get("run_scanner")
    if not tryb:
        return

    st.session_state.run_scanner = None

    if tryb == "quick":
        uni = SCANNER_UNIVERSE_QUICK
        st.info("⚡ Szybki skan (~200 spolek, kilka minut)...")
    else:
        uni = SCANNER_UNIVERSE_FULL
        st.info("🔬 Pelny skan (~300 spolek, kilkanascie minut)...")

    sdf, bledy = uruchom_skaner(uni)

    if sdf is None:
        st.error("Skan nie zwrocil zadnych danych.")
        return

    st.session_state.scanner_df = sdf
    oznacz_skan()
    st.success(f"✅ Zeskanowano {len(sdf)} spolek (pominieto {bledy}).")


def _filtr_rynku(sdf):
    """Filtr GPW / USA / EUROPA."""
    c1, _ = st.columns(2)
    with c1:
        rynek = st.selectbox("Filtruj rynek:",
                             ["Wszystkie"] + sorted(sdf["Rynek"].unique().tolist()),
                             key="scanner_rynek")
    if rynek == "Wszystkie":
        return sdf.copy()
    return sdf[sdf["Rynek"] == rynek].copy()


def _render_lista(dane, kolumny, tytul, sort_col, ascending=False, tab_id="tab", ile=20):
    """Wspolny renderer listy kart."""
    st.markdown(f"### {tytul}")
    if len(dane) == 0:
        st.info("Brak spolek spelniajacych kryteria.")
        return

    posortowane = dane.sort_values(sort_col, ascending=ascending).head(ile)
    for idx, (_, row) in enumerate(posortowane.iterrows()):
        render_karta(row, kolumny, tab_id=tab_id, idx=idx)


def _wzrosty(sdf):
    okres = st.radio("Okres:", list(OKRESY), horizontal=True, key="wzrost_int")
    col = OKRESY[okres]
    dane = sdf[sdf[col].notna() & (sdf[col] > 0)]
    _render_lista(dane, [(col, f"Zmiana {okres} %"), ("Wolumen%", "Wol %"),
                         ("RSI", "RSI"), ("MACD", "MACD")],
                  f"🚀 TOP wzrosty ({okres})", col, False, "wzrosty")


def _spadki(sdf):
    okres = st.radio("Okres:", list(OKRESY), horizontal=True, key="spadek_int")
    col = OKRESY[okres]
    dane = sdf[sdf[col].notna() & (sdf[col] < 0)]
    _render_lista(dane, [(col, f"Zmiana {okres} %"), ("Wolumen%", "Wol %"),
                         ("Od_High%", "Od 52W High %"), ("RSI", "RSI")],
                  f"💥 TOP spadki ({okres}) - potencjalne okazje", col, True, "spadki")


def _wolumen(sdf):
    st.caption("Nietypowa aktywnosc czesto poprzedza duzy ruch ceny.")
    prog = st.slider("Min. wzrost wolumenu (%)", 100, 500, 150, step=50, key="wol_slider")
    dane = sdf[sdf["Wolumen%"].notna() & (sdf["Wolumen%"] > prog)]
    if len(dane) == 0:
        st.warning(f"Brak spolek z wolumenem >{prog}%. Pokazuje TOP 20.")
        dane = sdf[sdf["Wolumen%"].notna()].nlargest(20, "Wolumen%")
    _render_lista(dane, [("Wolumen%", "Wol %"), ("1D%", "Zmiana 1D %"),
                         ("1T%", "Zmiana 1T %"), ("RSI", "RSI")],
                  f"📊 Nietypowy wolumen (>{prog}%)", "Wolumen%", False, "wolumen")


def _high52(sdf):
    st.caption("Spolki blisko rocznych szczytow - sygnal silnego trendu.")
    prog = st.slider("Max odleglosc od 52W High (%)", -20, 0, -5, key="high_slider")
    dane = sdf[sdf["Od_High%"].notna() & (sdf["Od_High%"] >= prog)]
    if len(dane) == 0:
        st.warning("Brak spolek. Pokazuje 20 najblizej szczytu.")
        dane = sdf[sdf["Od_High%"].notna()].nlargest(20, "Od_High%")
    _render_lista(dane, [("Od_High%", "Od 52W High %"), ("1M%", "Zmiana 1M %"),
                         ("52W_High", "52W High"), ("RSI", "RSI")],
                  "🏆 Blisko 52-week HIGH", "Od_High%", False, "high")


def _low52(sdf):
    st.caption("Spolki blisko rocznych dolkow - potencjalne okazje kontrariańskie.")
    prog = st.slider("Max odleglosc od 52W Low (%)", 0, 50, 15, step=5, key="low_slider")
    dane = sdf[sdf["Od_Low%"].notna() & (sdf["Od_Low%"] <= prog)]
    if len(dane) == 0:
        st.warning("Brak spolek. Pokazuje 20 najblizej dolka.")
        dane = sdf[sdf["Od_Low%"].notna()].nsmallest(20, "Od_Low%")
    _render_lista(dane, [("Od_Low%", "Od 52W Low %"), ("1M%", "Zmiana 1M %"),
                         ("52W_Low", "52W Low"), ("RSI", "RSI")],
                  f"📉 Blisko 52-week LOW (max +{prog}%)", "Od_Low%", True, "low")


def _tanie(sdf):
    st.caption("Spolki niedowartosciowane fundamentalnie.")
    c1, c2 = st.columns(2)
    with c1:
        max_pe = st.slider("Max P/E", 5, 30, 20, key="pe_slider")
    with c2:
        min_roe = st.slider("Min ROE (%)", 0, 30, 5, key="roe_slider")

    dane = sdf[sdf["PE"].notna() & (sdf["PE"] > 0) & (sdf["PE"] < max_pe)]
    if min_roe > 0:
        z_roe = dane[dane["ROE"].notna() & (dane["ROE"] > min_roe)]
        if len(z_roe) > 0:
            dane = z_roe
    if len(dane) == 0:
        st.warning("Brak spolek. Pokazuje najtansze wg P/E.")
        dane = sdf[sdf["PE"].notna() & (sdf["PE"] > 0)].nsmallest(20, "PE")

    _render_lista(dane, [("PE", "P/E"), ("ROE", "ROE %"),
                         ("1M%", "Zmiana 1M %"), ("MCap_mld", "MCap mld")],
                  f"💎 Tanie (P/E<{max_pe}, ROE>{min_roe}%)", "PE", True, "tanie")


def _momentum(sdf):
    st.caption("Spolki z silnym trendem technicznym.")
    typ = st.radio("Typ momentum:",
                   ["Silny trend", "Wybuchowe", "Wszystkie z trendem"],
                   horizontal=True, key="mom_type")

    if typ == "Silny trend":
        dane = sdf[sdf["RSI"].notna() & (sdf["RSI"] >= 45) & (sdf["RSI"] <= 65) &
                   (sdf["MACD"] == "BULL") & (sdf["Nad_SMA200"] == True)]
        opis = "🔥 Silny trend (RSI 45-65 + MACD BULL + nad SMA200)"
    elif typ == "Wybuchowe":
        dane = sdf[sdf["RSI"].notna() & (sdf["RSI"] > 60) & (sdf["RSI"] < 80) &
                   (sdf["MACD"] == "BULL") & sdf["1M%"].notna() & (sdf["1M%"] > 5)]
        opis = "🚀 Wybuchowe momentum (RSI 60-80 + MACD BULL + 1M >5%)"
    else:
        dane = sdf[(sdf["MACD"] == "BULL") & (sdf["Nad_SMA200"] == True)]
        opis = "📈 Trend (MACD BULL + nad SMA200)"

    if len(dane) == 0:
        st.warning(f"Brak spolek dla '{typ}'. Pokazuje najlepsze 1M.")
        dane = sdf[sdf["1M%"].notna()].nlargest(20, "1M%")

    _render_lista(dane, [("1M%", "Zmiana 1M %"), ("RSI", "RSI"),
                         ("MACD", "MACD"), ("Nad_SMA200", "Nad SMA200")],
                  opis, "1M%", False, "momentum")


def _eksport(sdf):
    st.markdown("### 📥 Eksport wynikow skanu")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Pobierz CSV", exp.do_csv(sdf),
                           exp.nazwa_pliku("skaner_okazji", "csv"), exp.MIME_CSV)
    with c2:
        st.download_button("📊 Pobierz Excel", exp.do_excel(sdf, "Skaner"),
                           exp.nazwa_pliku("skaner_okazji", "xlsx"), exp.MIME_EXCEL)


def _pomoc():
    st.markdown("""
    #### Co znajdzie skaner
    - 🚀 **Wzrosty** - spolki, ktore najbardziej urosly (1D / 1T / 1M / 3M)
    - 💥 **Spadki** - duze przeceny bywaja okazja kupna
    - 📊 **Wolumen** - nietypowa aktywnosc sugeruje, ze cos sie dzieje
    - 🏆 **52W High** - blisko rocznych szczytow (silny trend)
    - 📉 **52W Low** - blisko rocznych dolkow (potencjalne okazje)
    - 💎 **Tanie** - niskie P/E przy przyzwoitym ROE
    - 🔥 **Momentum** - RSI + MACD + SMA200 razem
    """)
