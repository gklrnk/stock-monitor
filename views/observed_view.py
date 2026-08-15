"""
OBSERVED VIEW - Zakladka "Obserwowane spolki"

Pokazuje pelna analize fundamentalno-techniczna listy obserwowanych:
- podsumowanie sygnalow (KUPUJ / OBSERWUJ / TRZYMAJ / OSTROZNIE / UNIKAJ)
- filtry (rynek, sygnal, minimalny score)
- TOP 15, pelna tabela, wykresy, gleboka analiza pojedynczej spolki, eksport

Cala logika liczenia siedzi w services/ - tutaj jest wylacznie widok.
"""

import streamlit as st
import yfinance as yf

from services import export_service as exp
from services.basket_service import czy_w_koszyku, dodaj_do_koszyka
from services.chart_service import (
    wykres_techniczny, wykres_top_score,
    wykres_momentum_score, wykres_rozklad_sygnalow,
)
from services.runner_service import uruchom_analize_obserwowanych
from utils.formatting import fmt_num, fmt_pct, opis_rekomendacji_analitykow
from utils.session_state import get_all_tickers, oznacz_analize

KOLUMNY_TABELI = [
    "Ticker", "Nazwa", "Rynek", "Cena", "1T%", "1M%", "3M%",
    "PE", "ROE", "Dywidenda", "RSI", "MACD", "SYGNAL", "Score", "Powody",
]


def render():
    """Punkt wejscia zakladki."""
    _obsluz_uruchomienie()

    if st.session_state.df is None:
        st.info("👈 Kliknij **Analiza obserwowanych** w panelu bocznym, "
                "aby pobrac dane i policzyc rekomendacje.")
        _pomoc()
        return

    df = st.session_state.df
    _podsumowanie(df)
    filtered = _filtry(df)

    t1, t2, t3, t4, t5 = st.tabs(
        ["🏆 TOP 15", "📋 Tabela", "📊 Wykresy", "🔍 Analiza spolki", "📥 Eksport"]
    )
    with t1:
        _top15(filtered)
    with t2:
        _tabela(filtered)
    with t3:
        _wykresy(filtered)
    with t4:
        _gleboka_analiza(df)
    with t5:
        _eksport(df)


def _obsluz_uruchomienie():
    """Uruchamia analize gdy w sidebarze wcisnieto przycisk."""
    if not st.session_state.get("run_scan"):
        return

    st.session_state.run_scan = False
    spolki = get_all_tickers()

    if not spolki:
        st.warning("Lista obserwowanych jest pusta - dodaj spolki w panelu bocznym.")
        return

    st.info(f"🔄 Analizuje {len(spolki)} obserwowanych spolek...")
    df, bledy = uruchom_analize_obserwowanych(
        spolki, universe_moje=st.session_state.UNIVERSE.get("MOJE", {})
    )

    if df is None:
        st.error("Nie udalo sie pobrac danych dla zadnej spolki.")
        return

    st.session_state.df = df
    oznacz_analize()
    st.success(f"✅ Przeanalizowano {len(df)} spolek.")
    if bledy:
        st.warning(f"Brak danych dla: {', '.join(bledy)}")


def _podsumowanie(df):
    """Liczniki sygnalow."""
    st.markdown("### 📈 Podsumowanie")
    c = st.columns(5)
    for kol, (etykieta, fraza) in zip(c, [
        ("🟢 Kupuj", "KUPUJ"), ("🔵 Obserwuj", "OBSERWUJ"),
        ("⚪ Trzymaj", "TRZYMAJ"), ("🟡 Ostroznie", "OSTROZNIE"),
        ("🔴 Unikaj", "UNIKAJ"),
    ]):
        kol.metric(etykieta, int(df["SYGNAL"].str.contains(fraza, na=False).sum()))

    if st.session_state.get("last_scan"):
        st.caption(f"Dane z: {st.session_state.last_scan}")


def _filtry(df):
    """Filtry rynku, sygnalu i minimalnego score."""
    st.markdown("---")
    st.markdown("### 🔍 Filtry")
    f1, f2, f3 = st.columns(3)

    with f1:
        rynek = st.selectbox("Rynek", ["Wszystkie"] + sorted(df["Rynek"].unique().tolist()))
    with f2:
        sygnal = st.selectbox("Sygnal", ["Wszystkie"] + df["SYGNAL"].unique().tolist())
    with f3:
        min_score = st.slider("Min. Score %", 0, 100, 0)

    filtered = df.copy()
    if rynek != "Wszystkie":
        filtered = filtered[filtered["Rynek"] == rynek]
    if sygnal != "Wszystkie":
        filtered = filtered[filtered["SYGNAL"] == sygnal]
    return filtered[filtered["Score"] >= min_score]


def _top15(filtered):
    """Lista TOP 15 rekomendacji z przyciskiem dodania do koszyka."""
    st.markdown("### 🏆 TOP 15 rekomendacji")
    if len(filtered) == 0:
        st.info("Brak spolek spelniajacych filtry.")
        return

    for i, r in filtered.head(15).reset_index(drop=True).iterrows():
        naglowek = (f"#{i + 1} {r['SYGNAL']} | {r['Nazwa']} ({r['Ticker']}) "
                    f"| Score: {r['Score']}%")
        with st.expander(naglowek):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cena", fmt_num(r["Cena"]))
            c2.metric("1M", fmt_pct(r["1M%"]))
            c3.metric("P/E", fmt_num(r["PE"], 1))
            c4.metric("RSI", fmt_num(r["RSI"], 1))

            st.markdown(f"**Powody:** {r['Powody'] or '-'}")
            st.markdown(
                f"**Rekomendacja analitykow:** "
                f"{opis_rekomendacji_analitykow(r.get('RekAnalit'))} "
                f"(cel: {fmt_num(r.get('CelAnalit'))}, "
                f"analitykow: {r.get('LiczbaAnal') or '-'})"
            )

            if czy_w_koszyku(r["Ticker"]):
                st.caption("⭐ juz w koszyku")
            elif st.button("⭐ Dodaj do koszyka", key=f"obs_top_{r['Ticker']}_{i}"):
                ok, msg = dodaj_do_koszyka(r["Ticker"], r["Nazwa"])
                st.success(msg) if ok else st.warning(msg)


def _tabela(filtered):
    """Pelna tabela z gradientem na kolumnie Score."""
    st.markdown(f"### 📋 Tabela ({len(filtered)} spolek)")
    kolumny = [k for k in KOLUMNY_TABELI if k in filtered.columns]
    st.dataframe(
        filtered[kolumny].style
        .background_gradient(subset=["Score"], cmap="RdYlGn")
        .format(precision=2, na_rep="-"),
        width="stretch", height=600,
    )


def _wykresy(filtered):
    """Trzy wykresy przegladowe."""
    st.markdown("### 📊 Wykresy")
    if len(filtered) == 0:
        st.info("Brak danych do wykresow.")
        return

    st.plotly_chart(wykres_top_score(filtered), width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(wykres_momentum_score(filtered), width="stretch")
    with c2:
        st.plotly_chart(wykres_rozklad_sygnalow(filtered), width="stretch")


def _gleboka_analiza(df):
    """Szczegolowy widok jednej spolki + wykres techniczny."""
    st.markdown("### 🔍 Gleboka analiza spolki")
    wszystkie = get_all_tickers()
    if not wszystkie:
        st.info("Brak obserwowanych spolek.")
        return

    wybor = st.selectbox(
        "Wybierz spolke:", list(wszystkie.keys()),
        format_func=lambda x: f"{x} - {wszystkie.get(x, '')}",
        key="obs_deep_select",
    )
    if not wybor:
        return

    with st.spinner("Pobieram dane z Yahoo Finance..."):
        stock = yf.Ticker(wybor)
        hist = stock.history(period="2y")
        info = stock.info if hasattr(stock, "info") else {}

    if hist is None or hist.empty:
        st.error("Brak danych historycznych dla tej spolki.")
        return

    nazwa = wszystkie.get(wybor, wybor)
    st.markdown(f"## {nazwa} ({wybor})")

    rzad = df[df["Ticker"] == wybor]
    if len(rzad) > 0:
        r = rzad.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Sygnal", r["SYGNAL"])
        c2.metric("Score", f"{r['Score']}%")
        c3.metric("Cena", fmt_num(r["Cena"]))

        st.markdown("#### 💰 Zmiany ceny")
        zc = st.columns(5)
        for kol, (etykieta, klucz) in zip(zc, [
            ("1T", "1T%"), ("1M", "1M%"), ("3M", "3M%"), ("6M", "6M%"), ("1R", "1R%")
        ]):
            kol.metric(etykieta, fmt_pct(r.get(klucz)))

        st.markdown("#### 📊 Fundamenty")
        fc = st.columns(5)
        for kol, (etykieta, klucz) in zip(fc, [
            ("P/E", "PE"), ("P/BV", "PBV"), ("ROE %", "ROE"),
            ("Marza %", "Marza"), ("Dyw. %", "Dywidenda"),
        ]):
            kol.metric(etykieta, fmt_num(r.get(klucz), 2))

        st.markdown(f"**💡 Powody:** {r['Powody'] or '-'}")
    else:
        st.info("Ta spolka nie byla jeszcze w ostatniej analizie - "
                "uruchom **Analiza obserwowanych**, aby zobaczyc scoring.")

    st.markdown("#### 📈 Wykres techniczny")
    st.plotly_chart(
        wykres_techniczny(hist, nazwa, target=info.get("targetMeanPrice")),
        width="stretch",
    )


def _eksport(df):
    """Pobieranie wynikow analizy."""
    st.markdown("### 📥 Eksport danych")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Pobierz CSV", exp.do_csv(df),
                           exp.nazwa_pliku("analiza_obserwowanych", "csv"),
                           exp.MIME_CSV)
    with c2:
        st.download_button("📊 Pobierz Excel", exp.do_excel(df, "Analiza"),
                           exp.nazwa_pliku("analiza_obserwowanych", "xlsx"),
                           exp.MIME_EXCEL)


def _pomoc():
    """Krotki opis co robi zakladka."""
    st.markdown("""
    #### Co znajdziesz w tej zakladce
    - **Scoring 0-100%** liczony z fundamentow (P/E, P/BV, ROE, marza, dywidenda,
      zadluzenie, wzrost przychodow), techniki (RSI, MACD, SMA200) i momentum
    - **Sygnal**: 🟢 KUPUJ / 🔵 OBSERWUJ / ⚪ TRZYMAJ / 🟡 OSTROZNIE / 🔴 UNIKAJ
    - **Zmiany**: tydzien, miesiac, kwartal, pol roku, rok
    - **Rekomendacje analitykow** i cena docelowa z Yahoo Finance
    """)
