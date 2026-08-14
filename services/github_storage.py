"""
GITHUB STORAGE - Trwaly zapis danych w prywatnym repo GitHub

Ten modul odpowiada za synchronizacje danych miedzy urzadzeniami.
Wszystkie dane (koszyk, portfolio, transakcje) sa zapisywane
w Twoim prywatnym repo stock-data w postaci plikow JSON.

Wymaga konfiguracji w Streamlit Secrets:
    [github]
    token = "github_pat_..."
    username = "twoj_login"
    data_repo = "stock-data"

Uzywane w: basket_service.py, portfolio_service.py
"""

import streamlit as st
import json
import base64
import requests
from datetime import datetime


def _get_config():
    """Pobiera konfiguracje GitHub z Streamlit Secrets."""
    try:
        token = st.secrets["github"]["token"]
        username = st.secrets["github"]["username"]
        data_repo = st.secrets["github"]["data_repo"]
        return token, username, data_repo
    except:
        return None, None, None


def _get_headers(token):
    """Buduje naglowki HTTP dla GitHub API."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def zapisz_dane(nazwa_pliku, dane):
    """
    Zapisuje dane do pliku JSON w prywatnym repo GitHub.
    
    :param nazwa_pliku: np. "basket.json", "portfolio.json"
    :param dane: slownik lub lista do zapisu
    :return: True jesli sukces, False jesli blad
    
    Przyklad:
        zapisz_dane("basket.json", {"tickers": ["NVDA", "CDR.WA"]})
    """
    token, username, data_repo = _get_config()
    if not token:
        st.error("Brak konfiguracji GitHub w Streamlit Secrets!")
        return False
    
    try:
        url = f"https://api.github.com/repos/{username}/{data_repo}/contents/data/{nazwa_pliku}"
        headers = _get_headers(token)
        
        # Sprawdz czy plik istnieje (potrzebne SHA do update)
        sha = None
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                sha = response.json().get("sha")
        except:
            pass
        
        # Przygotuj tresc do zapisu
        json_string = json.dumps(dane, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Update {nazwa_pliku} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
        
        # Zapisz plik
        response = requests.put(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code in [200, 201]:
            return True
        else:
            st.warning(f"GitHub zwrocil status {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        st.error(f"Blad zapisu do GitHub: {e}")
        return False


def wczytaj_dane(nazwa_pliku, domyslne=None):
    """
    Wczytuje dane z pliku JSON z prywatnego repo GitHub.
    
    :param nazwa_pliku: np. "basket.json", "portfolio.json"
    :param domyslne: co zwrocic jesli plik nie istnieje (np. {} lub [])
    :return: dane z pliku lub wartosc domyslna
    
    Przyklad:
        koszyk = wczytaj_dane("basket.json", domyslne={"tickers": []})
    """
    if domyslne is None:
        domyslne = {}
    
    token, username, data_repo = _get_config()
    if not token:
        return domyslne
    
    try:
        url = f"https://api.github.com/repos/{username}/{data_repo}/contents/data/{nazwa_pliku}"
        headers = _get_headers(token)
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            # Plik nie istnieje - zwroc domyslne
            return domyslne
        
        if response.status_code != 200:
            st.warning(f"GitHub: {response.status_code}")
            return domyslne
        
        # Zdekoduj tresc z base64
        content_b64 = response.json().get("content", "")
        content_bytes = base64.b64decode(content_b64)
        content_str = content_bytes.decode("utf-8")
        
        return json.loads(content_str)
        
    except Exception as e:
        # Jesli blad - zwroc domyslne (aplikacja nie moze zawiesic sie)
        return domyslne


def usun_plik(nazwa_pliku):
    """
    Usuwa plik z prywatnego repo GitHub.
    
    :param nazwa_pliku: np. "basket.json"
    :return: True jesli sukces
    """
    token, username, data_repo = _get_config()
    if not token:
        return False
    
    try:
        url = f"https://api.github.com/repos/{username}/{data_repo}/contents/data/{nazwa_pliku}"
        headers = _get_headers(token)
        
        # Pobierz SHA
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        
        sha = response.json().get("sha")
        
        # Usun
        payload = {
            "message": f"Delete {nazwa_pliku}",
            "sha": sha,
            "branch": "main"
        }
        
        response = requests.delete(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
        
    except:
        return False


def czy_skonfigurowany():
    """
    Sprawdza czy GitHub Storage jest poprawnie skonfigurowany.
    
    :return: True jesli mozna zapisywac/wczytywac
    """
    token, username, data_repo = _get_config()
    return bool(token and username and data_repo)


def status_polaczenia():
    """
    Testuje polaczenie z GitHub API.
    
    :return: (bool, str) - czy dziala, komunikat
    """
    token, username, data_repo = _get_config()
    
    if not token:
        return False, "Brak tokena w Streamlit Secrets"
    
    try:
        url = f"https://api.github.com/repos/{username}/{data_repo}"
        headers = _get_headers(token)
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return True, f"Polaczono z {username}/{data_repo}"
        elif response.status_code == 404:
            return False, f"Nie znaleziono repo {data_repo}"
        elif response.status_code == 401:
            return False, "Nieprawidlowy token GitHub"
        else:
            return False, f"GitHub status: {response.status_code}"
            
    except Exception as e:
        return False, f"Blad polaczenia: {e}"
