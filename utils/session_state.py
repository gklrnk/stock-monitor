"""
Zarządzanie stanem sesji Streamlit.
"""
import streamlit as st
from config.universe import UNIVERSE_DEFAULT

def init_session_state():
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
    if "basket" not in st.session_state:
        from services.basket_service import wczytaj_koszyk
        st.session_state.basket = wczytaj_koszyk()
