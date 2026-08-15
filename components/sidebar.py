import streamlit as st
import time
import yfinance as yf

def render_sidebar():
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
        st.markdown("### ➕ Dodaj spółkę do obserwowanych")
        with st.form("dodaj_form"):
            new_ticker = st.text_input("Ticker (np. AAPL, CCC.WA)", key="new_ticker")
            new_nazwa = st.text_input("Nazwa (opcjonalnie)", key="new_nazwa")
            if st.form_submit_button("➕ Dodaj") and new_ticker:
                ticker = new_ticker.upper().strip()
                try:
                    s = yf.Ticker(ticker)
                    if s.history(period="5d").empty:
                        st.error(f"❌ Nie znaleziono {ticker}")
                    else:
                        nazwa = new_nazwa if new_nazwa else (s.info.get("shortName") or ticker)
                        st.session_state.UNIVERSE["MOJE"][ticker] = nazwa
                        st.success(f"✅ Dodano: {nazwa}")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")
