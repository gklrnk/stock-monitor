"""
BASKET VIEW - Zakladka "Koszyk analityczny"

Koszyk to shortlista max 10 spolek do glebokiej analizy przed decyzja.
Zapisuje sie automatycznie (GitHub lub dysk), wiec wybor zrobiony
wieczorem na komputerze widac rano na telefonie.

Podzakladki:
- Moje spolki: lista z notatkami, usuwanie, szybki podglad
- Analiza porownawcza: tabela scoringu wszystkich spolek z koszyka
- Wykresy: swiece dla wybranej + porownanie stop zwrotu
- Newsy: wspolny feed dla calego koszyka
- Presety: zapisane zestawy koszykow
"""

import time

import pandas as pd
import streamlit as st
import yfinance as yf

from services import export_service as exp
from services.basket_service import (
    MAX_BASKET_SIZE, dodaj_do_koszyka, usun_z_koszyka, wyczysc_koszyk,
    aktualizuj_notatke, pobierz_tickery_z_koszyka, liczba_w_koszyku,
    wczytaj_presety, zapisz_preset, wczytaj_preset, usun_preset,
)
from services.chart_service import wykres_techniczny, wykres_porownanie_cen
from services.news_service import pobierz_newsy_dla_wielu
from services.runner_service import analizuj_liste
from utils.formatting import fmt_num, fmt_pct
from utils.session_state import get_all_tickers, dodaj_do_obserwowanych


def render():
    """Punkt wejscia zakladki."""
    st.markdown("### ⭐ Koszyk analityczny")
    st.caption(f"Twoja shortlista do glebokiej analizy "
               f"({liczba_w_koszyku()}/{MAX_BASKET_SIZE} spolek). "
               f"Zapisuje sie automatycznie i dziala z kazdego urzadzenia.")

    _dodawanie_reczne()

    koszyk = st.session_state.get("basket", [])
    if not koszyk:
        st.info("Koszyk jest pusty. Dodaj spolki ze **Skanera okazji**, "
                "z **Obserwowanych** albo recznie powyzej.")
        return

    t1, t2, t3, t4, t5 = st.tabs([
        "📋 Moje spolki", "⚖️ Analiza porownawcza",
        "📈 Wykresy", "📰 Newsy", "💾 Presety",
    ])
    with t1:
        _lista(koszyk)
    with t2:
        _porownanie(koszyk)
    with t3:
        _wykresy(koszyk)
    with t4:
        _newsy(koszyk)
    with t5:
        _presety()


def _dodawanie_reczne():
    """Formularz dodania spolki po tickerze."""
    with st.expander("➕ Dodaj spolke recznie (po tickerze)"):
        with st.form("basket_add"):
            c1, c2 = st.columns(2)
            with c1:
                ticker = st.text_input("Ticker (np. NVDA, CDR.WA)")
            with c2:
                notatka = st.text_input("Notatka (opcjonalnie)")
            if st.form_submit_button("⭐ Dodaj do koszyka") and ticker:
                t = ticker.upper().strip()
                nazwa = get_all_tickers().get(t)
                if not nazwa:
                    try:
                        nazwa = yf.Ticker(t).info.get("shortName") or t
                    except Exception:
                        nazwa = t
                ok, msg = dodaj_do_koszyka(t, nazwa, notatka)
                if ok:
                    st.success(msg)
                    time.sleep(0.6)
                    st.rerun()
                else:
                    st.warning(msg)


def _lista(koszyk):
    """Lista spolek w koszyku z notatkami i akcjami."""
    st.markdown(f"#### Spolki w koszyku ({len(koszyk)}/{MAX_BASKET_SIZE})")

    for i, item in enumerate(koszyk):
        ticker, nazwa = item["ticker"], item["nazwa"]
        with st.container():
            c1, c2, c3 = st.columns([4, 3, 2])
            with c1:
                st.markdown(f"**{nazwa}** ({ticker})")
                st.caption(f"Dodano: {item.get('dodano', '-')}")
            with c2:
                nowa = st.text_input("Notatka", value=item.get("notatka", ""),
                                     key=f"nota_{ticker}_{i}",
                                     label_visibility="collapsed",
                                     placeholder="Notatka...")
                if nowa != item.get("notatka", ""):
                    aktualizuj_notatke(ticker, nowa)
            with c3:
                if ticker not in get_all_tickers():
                    if st.button("➕ Obserwuj", key=f"bobs_{ticker}_{i}"):
                        dodaj_do_obserwowanych(ticker, nazwa)
                        st.rerun()
                else:
                    st.caption("✅ obserwowane")
                if st.button("🗑️ Usun", key=f"bdel_{ticker}_{i}"):
                    ok, msg = usun_z_koszyka(ticker)
                    st.success(msg) if ok else st.warning(msg)
                    time.sleep(0.5)
                    st.rerun()
            st.markdown("---")

    if st.button("🧹 Wyczysc caly koszyk"):
        wyczysc_koszyk()
        st.rerun()


def _porownanie(koszyk):
    """Pelna analiza scoringowa wszystkich spolek z koszyka."""
    st.markdown("#### ⚖️ Analiza porownawcza")
    st.caption("Pelny scoring (fundamenty + technika) dla spolek z koszyka.")

    if st.button("🔍 Przeanalizuj koszyk", key="basket_analyze"):
        pary = [(i["ticker"], i["nazwa"]) for i in koszyk]
        with st.spinner(f"Analizuje {len(pary)} spolek..."):
            df = analizuj_liste(pary)
        if df is None:
            st.error("Nie udalo sie pobrac danych.")
            return
        st.session_state["basket_df"] = df

    df = st.session_state.get("basket_df")
    if df is None:
        st.info("Kliknij przycisk, aby policzyc scoring dla koszyka.")
        return

    kolumny = [k for k in ["Ticker", "Nazwa", "Cena", "1T%", "1M%", "3M%", "PE",
                           "PBV", "ROE", "Marza", "Dywidenda", "RSI", "MACD",
                           "SYGNAL", "Score"] if k in df.columns]
    st.dataframe(
        df[kolumny].style.background_gradient(subset=["Score"], cmap="RdYlGn")
        .format(precision=2, na_rep="-"),
        width="stretch",
    )

    st.markdown("##### Werdykt")
    for _, r in df.iterrows():
        st.markdown(f"- {r['SYGNAL']} **{r['Nazwa']}** ({r['Ticker']}) "
                    f"– Score {r['Score']}% | Cena {fmt_num(r['Cena'])} | "
                    f"1M {fmt_pct(r['1M%'])} | {r['Powody'] or '-'}")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 CSV", exp.do_csv(df),
                           exp.nazwa_pliku("koszyk", "csv"), exp.MIME_CSV)
    with c2:
        st.download_button("📊 Excel", exp.do_excel(df, "Koszyk"),
                           exp.nazwa_pliku("koszyk", "xlsx"), exp.MIME_EXCEL)


def _wykresy(koszyk):
    """Wykres techniczny wybranej spolki + porownanie stop zwrotu."""
    st.markdown("#### 📈 Wykresy")
    tickery = [i["ticker"] for i in koszyk]
    nazwy = {i["ticker"]: i["nazwa"] for i in koszyk}

    wybor = st.selectbox("Spolka:", tickery,
                         format_func=lambda t: f"{t} - {nazwy.get(t, '')}",
                         key="basket_chart_select")
    okres = st.select_slider("Okres:", ["6mo", "1y", "2y", "5y"], value="1y",
                             key="basket_chart_period")

    if wybor:
        with st.spinner("Pobieram dane..."):
            stock = yf.Ticker(wybor)
            hist = stock.history(period=okres)
            info = stock.info if hasattr(stock, "info") else {}
        if hist is not None and not hist.empty:
            st.plotly_chart(
                wykres_techniczny(hist, nazwy.get(wybor, wybor),
                                  target=info.get("targetMeanPrice")),
                width="stretch",
            )
        else:
            st.error("Brak danych historycznych.")

    st.markdown("##### Porownanie stop zwrotu (caly koszyk)")
    if st.button("📊 Porownaj wszystkie", key="basket_compare"):
        dane = {}
        with st.spinner("Pobieram ceny..."):
            for t in tickery:
                try:
                    h = yf.Ticker(t).history(period=okres)
                    if h is not None and not h.empty:
                        dane[t] = h["Close"]
                except Exception:
                    continue
        if dane:
            st.plotly_chart(wykres_porownanie_cen(dane), width="stretch")
        else:
            st.warning("Brak danych do porownania.")


def _newsy(koszyk):
    """Wspolny feed newsow dla calego koszyka."""
    st.markdown("#### 📰 Newsy dla koszyka")
    limit = st.slider("Newsow na spolke", 1, 10, 3, key="basket_news_limit")

    if not st.button("🔄 Pobierz newsy", key="basket_news_run"):
        st.info("Kliknij, aby pobrac najnowsze wiadomosci dla spolek z koszyka.")
        return

    with st.spinner("Pobieram newsy..."):
        newsy = pobierz_newsy_dla_wielu(pobierz_tickery_z_koszyka(),
                                        limit_na_spolke=limit)
    if not newsy:
        st.info("Brak dostepnych newsow.")
        return

    for n in newsy:
        st.markdown(f"**{n['date']}** | `{n.get('ticker', '')}` | *{n['publisher']}*")
        st.markdown(f"[{n['title']}]({n['link']})")
        st.markdown("---")


def _presety():
    """Zapisane zestawy koszykow."""
    st.markdown("#### 💾 Presety koszyka")
    st.caption("Zapisz aktualny zestaw pod nazwa i wracaj do niego jednym klikiem.")

    with st.form("preset_save"):
        nazwa = st.text_input("Nazwa presetu (np. banki_gpw, ai_stocks)")
        if st.form_submit_button("💾 Zapisz aktualny koszyk") and nazwa:
            ok, msg = zapisz_preset(nazwa.strip())
            st.success(msg) if ok else st.warning(msg)

    presety = wczytaj_presety()
    if not presety:
        st.caption("Brak zapisanych presetow.")
        return

    for nazwa, dane in presety.items():
        c1, c2, c3 = st.columns([4, 2, 2])
        with c1:
            tickery = [b["ticker"] for b in dane.get("basket", [])]
            st.markdown(f"**{nazwa}** – {', '.join(tickery) or 'pusty'}")
            st.caption(f"Utworzono: {dane.get('created_at', '-')}")
        with c2:
            if st.button("📂 Wczytaj", key=f"pload_{nazwa}"):
                ok, msg = wczytaj_preset(nazwa)
                st.success(msg) if ok else st.warning(msg)
                time.sleep(0.5)
                st.rerun()
        with c3:
            if st.button("🗑️ Usun", key=f"pdel_{nazwa}"):
                usun_preset(nazwa)
                st.rerun()
