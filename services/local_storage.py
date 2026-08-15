"""
LOCAL STORAGE - Zapasowy zapis danych na dysku lokalnym

Ten modul jest uzywany AUTOMATYCZNIE gdy nie skonfigurowano
tokena GitHub w Streamlit Secrets.

Dzieki temu aplikacja dziala od razu po uruchomieniu (dane leza
w folderze data/ obok kodu), a po dodaniu tokena GitHub
przelacza sie na synchronizacje miedzy urzadzeniami.

Uzywane w: github_storage.py (jako fallback)
"""

import json
import os
from datetime import datetime

# Folder na dane lokalne (tworzony automatycznie)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _sciezka(nazwa_pliku):
    """Zwraca pelna sciezke do pliku w folderze data/."""
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, nazwa_pliku)


def zapisz_lokalnie(nazwa_pliku, dane):
    """
    Zapisuje slownik/liste do pliku JSON w folderze data/.

    :param nazwa_pliku: np. "basket.json"
    :param dane: slownik lub lista
    :return: True jesli sukces
    """
    try:
        with open(_sciezka(nazwa_pliku), "w", encoding="utf-8") as f:
            json.dump(dane, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def wczytaj_lokalnie(nazwa_pliku, domyslne=None):
    """
    Wczytuje dane z pliku JSON w folderze data/.

    :param nazwa_pliku: np. "basket.json"
    :param domyslne: co zwrocic gdy pliku nie ma
    :return: dane lub wartosc domyslna
    """
    if domyslne is None:
        domyslne = {}
    try:
        sciezka = _sciezka(nazwa_pliku)
        if not os.path.exists(sciezka):
            return domyslne
        with open(sciezka, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return domyslne


def usun_lokalnie(nazwa_pliku):
    """Usuwa plik z folderu data/."""
    try:
        sciezka = _sciezka(nazwa_pliku)
        if os.path.exists(sciezka):
            os.remove(sciezka)
        return True
    except Exception:
        return False


def status_lokalny():
    """
    Zwraca informacje o lokalnym magazynie danych.

    :return: (bool, str)
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        pliki = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
        return True, f"Zapis lokalny: {DATA_DIR} ({len(pliki)} plikow JSON)"
    except Exception as e:
        return False, f"Blad zapisu lokalnego: {e}"


def ostatnia_zmiana(nazwa_pliku):
    """Zwraca date ostatniej modyfikacji pliku lub None."""
    try:
        sciezka = _sciezka(nazwa_pliku)
        if os.path.exists(sciezka):
            ts = os.path.getmtime(sciezka)
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return None
