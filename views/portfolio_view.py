"""
PORTFOLIO VIEW - Zakladka "Portfolio"

Sledzenie wlasnego portfela:
- dodawanie transakcji kupna i sprzedazy
- aktualne pozycje z wycena real-time
- zysk niezrealizowany i zrealizowany (FIFO)
- statystyki (win rate, najlepsza / najgorsza pozycja)
- historia transakcji i eksport

Logika liczenia siedzi w services/portfolio_service.py.
"""

import time
from datetime import date

import pandas as pd
import streamlit as st

from services import export_service as exp
from services.chart_service import wykres_struktura_portfela, wykres_zysk_pozycji
from services.portfolio_service import (
    dodaj_transakcje, usun_transakcje, wczytaj_transakcje,
    pobierz_pozycje_z_wycena, podsumowanie_portfela,
    zysk_zrealizowany, statystyki_zaawansowane,
    formatuj_walute, format_zysk,
)
from utils.formatting import fmt_num
from utils.session_state import get_all_tickers

WALUTY = ["PLN", "USD", "EUR", "GBP"]


def render():
    """Punkt wejscia zakladki."""
    st.markdown("### 💼 Portfolio")
    st.caption("Twoje realne pozycje, wycena i wyniki. "
               "Dane zapisuja sie automatycznie (GitHub lub dysk lokalny).")

    t1, t2, t3, t4, t5 = st.tabs([
        "📊 Przeglad", "➕ Nowa transakcja", "📈 Statystyki",
        "📜 Historia", "📥 Eksport",
    ])
    with t1:
        _przeglad()
    with t2:
        _formularz()
    with t3:
        _statystyki()
    with t4:
        _historia()
    with t5:
        _eksport()


def _przeglad():
    """Pozycje otwarte z wycena i wykresami."""
    if st.button("🔄 Odswiez wycene", key="pf_refresh"):
        st.session_state.portfolio_cache = None

    if st.session_state.get("portfolio_cache") is None:
        with st.spinner("Pobieram aktualne ceny..."):
            st.session_state.portfolio_cache = {
                "pozycje": pobierz_pozycje_z_wycena(),
                "podsumowanie": podsumowanie_portfela(),
            }

    cache = st.session_state.portfolio_cache
    pozycje = cache["pozycje"]
    pods = cache["podsumowanie"]

    if not pozycje:
        st.info("Portfel jest pusty. Dodaj pierwsza transakcje "
                "w zakladce **Nowa transakcja**.")
        return

    st.markdown("#### 💰 Podsumowanie")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pozycji otwartych", pods["liczba_pozycji"])
    c2.metric("Zainwestowano",
              formatuj_walute(pods["wartosc_zakupu_total"], pods["waluta"]))
    c3.metric("Wartosc aktualna",
              formatuj_walute(pods["wartosc_aktualna_total"], pods["waluta"]))
    c4.metric("Zysk niezrealizowany",
              formatuj_walute(pods["zysk_niezrealizowany"], pods["waluta"]),
              f"{pods['zysk_niezrealizowany_pct']:+.2f}%")

    if len(pods.get("wszystkie_waluty", {})) > 1:
        st.caption("⚠️ Portfel zawiera kilka walut - podsumowanie pokazuje "
                   "dominujaca. Rozbicie ponizej.")
        st.dataframe(pd.DataFrame(pods["wszystkie_waluty"]).T,
                     width="stretch")

    st.markdown("#### 📋 Pozycje")
    df = pd.DataFrame([{
        "Ticker": p["ticker"],
        "Nazwa": p["nazwa"],
        "Ilosc": p["ilosc"],
        "Srednia cena": p["srednia_cena"],
        "Aktualna cena": p.get("aktualna_cena"),
        "Wartosc zakupu": p.get("wartosc_zakupu"),
        "Wartosc aktualna": p.get("wartosc_aktualna"),
        "Zysk": p.get("zysk"),
        "Zysk %": p.get("zysk_pct"),
        "Waluta": p.get("waluta"),
    } for p in pozycje])

    st.dataframe(df.style.format(precision=2, na_rep="-"), width="stretch")

    for p in pozycje:
        st.markdown(
            f"- **{p['nazwa']}** ({p['ticker']}) | {p['ilosc']} szt. | "
            f"srednia {fmt_num(p['srednia_cena'])} → "
            f"aktualna {fmt_num(p.get('aktualna_cena'))} | "
            f"{format_zysk(p.get('zysk_pct'), procent=True)} "
            f"({formatuj_walute(p.get('zysk'), p.get('waluta', 'PLN'))})"
        )

    c1, c2 = st.columns(2)
    with c1:
        fig = wykres_struktura_portfela(pozycje)
        if fig:
            st.plotly_chart(fig, width="stretch")
    with c2:
        fig = wykres_zysk_pozycji(pozycje)
        if fig:
            st.plotly_chart(fig, width="stretch")


def _formularz():
    """Dodawanie transakcji kupna/sprzedazy."""
    st.markdown("#### ➕ Nowa transakcja")
    obserwowane = get_all_tickers()

    with st.form("pf_add"):
        c1, c2 = st.columns(2)
        with c1:
            typ = st.selectbox("Typ", ["KUPNO", "SPRZEDAZ"])
            ticker = st.text_input("Ticker (np. NVDA, PKO.WA)")
            nazwa = st.text_input("Nazwa (opcjonalnie - uzupelni sie sama)")
            waluta = st.selectbox("Waluta", WALUTY)
        with c2:
            ilosc = st.number_input("Ilosc akcji", min_value=1, value=1, step=1)
            cena = st.number_input("Cena za akcje", min_value=0.0,
                                   value=0.0, step=0.01, format="%.2f")
            prowizja = st.number_input("Prowizja", min_value=0.0,
                                       value=0.0, step=0.01, format="%.2f")
            data_tr = st.date_input("Data transakcji", value=date.today())

        notatka = st.text_input("Notatka (opcjonalnie)")

        if st.form_submit_button("💾 Zapisz transakcje"):
            if not ticker or cena <= 0:
                st.error("Podaj ticker i cene wieksza od zera.")
            else:
                t = ticker.upper().strip()
                pelna_nazwa = nazwa.strip() or obserwowane.get(t, t)
                ok, msg = dodaj_transakcje(
                    typ=typ, ticker=t, nazwa=pelna_nazwa,
                    ilosc=int(ilosc), cena=float(cena),
                    data=str(data_tr), prowizja=float(prowizja),
                    waluta=waluta, notatka=notatka,
                )
                if ok:
                    st.success(msg)
                    st.session_state.portfolio_cache = None
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error(msg)


def _statystyki():
    """Win rate, zysk zrealizowany, najlepsze/najgorsze pozycje."""
    st.markdown("#### 📈 Statystyki")
    with st.spinner("Licze..."):
        stats = statystyki_zaawansowane()
        zrealizowane = zysk_zrealizowany()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Win rate", f"{stats['win_rate']}%")
    c2.metric("Zysk zrealizowany", fmt_num(stats["zysk_zrealizowany"]))
    c3.metric("Pozycji otwartych", stats["otwarte_pozycje"])
    c4.metric("Transakcji razem", stats["total_transakcji"])

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Zyskownych zamkniec", stats["zyskowne_transakcje"])
    with c2:
        st.metric("Stratnych zamkniec", stats["stratne_transakcje"])

    najlepsza, najgorsza = stats["najlepsza_pozycja"], stats["najgorsza_pozycja"]
    if najlepsza:
        st.success(f"🏆 Najlepsza: {najlepsza['nazwa']} ({najlepsza['ticker']}) "
                   f"{format_zysk(najlepsza['zysk_pct'], procent=True)}")
    if najgorsza:
        st.error(f"🔴 Najgorsza: {najgorsza['nazwa']} ({najgorsza['ticker']}) "
                 f"{format_zysk(najgorsza['zysk_pct'], procent=True)}")

    st.markdown("##### 💵 Zamkniete pozycje (FIFO)")
    if zrealizowane:
        st.dataframe(pd.DataFrame(zrealizowane).style.format(precision=2, na_rep="-"),
                     width="stretch")
    else:
        st.caption("Brak zamknietych pozycji.")


def _historia():
    """Pelna historia transakcji z mozliwoscia usuniecia."""
    st.markdown("#### 📜 Historia transakcji")
    transakcje = wczytaj_transakcje()

    if not transakcje:
        st.info("Brak transakcji.")
        return

    for t in sorted(transakcje, key=lambda x: x["data"], reverse=True):
        c1, c2 = st.columns([6, 1])
        with c1:
            ikona = "🟢" if t["typ"] == "KUPNO" else "🔴"
            st.markdown(
                f"{ikona} **{t['data']}** | {t['typ']} | "
                f"{t['nazwa']} ({t['ticker']}) | {t['ilosc']} szt. @ "
                f"{fmt_num(t['cena'])} {t['waluta']} | "
                f"wartosc {fmt_num(t['wartosc'])}"
            )
            if t.get("notatka"):
                st.caption(t["notatka"])
        with c2:
            if st.button("🗑️", key=f"tdel_{t['id']}"):
                ok, msg = usun_transakcje(t["id"])
                if ok:
                    st.session_state.portfolio_cache = None
                    st.success(msg)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning(msg)
        st.markdown("---")


def _eksport():
    """Eksport pozycji i transakcji (np. do rozliczenia podatkowego)."""
    st.markdown("#### 📥 Eksport portfela")
    transakcje = wczytaj_transakcje()
    if not transakcje:
        st.info("Brak danych do eksportu.")
        return

    df_tr = pd.DataFrame(transakcje)
    df_zr = pd.DataFrame(zysk_zrealizowany())
    pozycje = (st.session_state.get("portfolio_cache") or {}).get("pozycje") or []
    df_poz = pd.DataFrame(pozycje)

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Transakcje CSV", exp.do_csv(df_tr),
                           exp.nazwa_pliku("transakcje", "csv"), exp.MIME_CSV)
    with c2:
        st.download_button(
            "📊 Portfolio Excel",
            exp.do_excel_wiele({
                "Pozycje": df_poz,
                "Transakcje": df_tr,
                "Zrealizowane": df_zr,
            }),
            exp.nazwa_pliku("portfolio", "xlsx"), exp.MIME_EXCEL,
        )
