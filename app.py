import streamlit as st

# Importujemy nasze moduły z serwisów i komponentów
from utils.session_state import init_session_state
from components.sidebar import render_sidebar
from pages.observed_page import render_observed_page
from pages.scanner_page import render_scanner_page
from pages.calendar_page import render_calendar_page
from pages.basket_page import render_basket_page
from pages.portfolio_page import render_portfolio_page

# Konfiguracja głównej strony
st.set_page_config(page_title="Stock Monitor", page_icon="📊", layout="wide")

# Uruchomienie stanu sesji (zmienne, słowniki, cache)
init_session_state()

# Wyrenderowanie panelu bocznego
render_sidebar()

# Nagłówek główny
st.markdown('<h1 style="text-align:center; color:#1e3c72;">📊 STOCK MONITOR & PORTFOLIO</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Architektura Mikroserwisowa | GPW + Global</p>", unsafe_allow_html=True)
st.markdown("---")

# Nawigacja i zakładki
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Obserwowane", 
    "🔎 Skaner Okazji", 
    "⭐ Koszyk", 
    "💼 Portfolio", 
    "📅 Kalendarz"
])

with tab1:
    render_observed_page()
with tab2:
    render_scanner_page()
with tab3:
    render_basket_page()
with tab4:
    render_portfolio_page()
with tab5:
    render_calendar_page()
