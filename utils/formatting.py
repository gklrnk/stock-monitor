"""
FORMATTING - Pomocnicze funkcje formatowania do interfejsu

Male, czysto prezentacyjne funkcje uzywane w zakladkach (views/).
Trzymamy je osobno, zeby widoki nie powtarzaly tego samego kodu.
"""

import pandas as pd


def fmt_pct(wartosc, znak=True):
    """
    Formatuje liczbe jako procent, np. 12.5 -> "+12.5%".

    :param wartosc: liczba lub None
    :param znak: czy dodawac + przy dodatnich
    """
    if wartosc is None or (isinstance(wartosc, float) and pd.isna(wartosc)):
        return "-"
    try:
        v = float(wartosc)
    except (TypeError, ValueError):
        return "-"
    return f"{v:+.2f}%" if znak else f"{v:.2f}%"


def fmt_num(wartosc, miejsca=2):
    """Formatuje liczbe lub zwraca '-' gdy brak danych."""
    if wartosc is None or (isinstance(wartosc, float) and pd.isna(wartosc)):
        return "-"
    try:
        return f"{float(wartosc):,.{miejsca}f}"
    except (TypeError, ValueError):
        return str(wartosc)


def kolor_zmiany(wartosc):
    """Zwraca nazwe koloru CSS zaleznie od znaku liczby."""
    try:
        v = float(wartosc)
    except (TypeError, ValueError):
        return "gray"
    if v > 0:
        return "green"
    if v < 0:
        return "red"
    return "gray"


def badge_zmiany(etykieta, wartosc):
    """
    Zwraca fragment HTML z kolorowa zmiana procentowa.

    Uzywane w kartach spolek w skanerze i koszyku.
    """
    if wartosc is None or (isinstance(wartosc, float) and pd.isna(wartosc)):
        return f"<small>{etykieta}: <b>-</b></small>"
    kolor = kolor_zmiany(wartosc)
    return f"<small>{etykieta}: <b style='color:{kolor}'>{float(wartosc):+.2f}%</b></small>"


# Kolory sygnalow - wspolne dla wykresow i tabel
KOLORY_SYGNALOW = {
    "🟢 KUPUJ": "#00aa00",
    "🔵 OBSERWUJ": "#3399ff",
    "⚪ TRZYMAJ": "#999999",
    "🟡 OSTROZNIE": "#ffaa00",
    "🔴 UNIKAJ": "#cc0000",
}


def opis_rekomendacji_analitykow(klucz):
    """
    Tlumaczy rekomendacje z Yahoo Finance na polski.

    :param klucz: np. "strong_buy", "hold"
    """
    mapa = {
        "strong_buy": "🟢 Zdecydowanie kupuj",
        "buy": "🟢 Kupuj",
        "hold": "⚪ Trzymaj",
        "underperform": "🟡 Gorzej niz rynek",
        "sell": "🔴 Sprzedaj",
        "none": "brak danych",
    }
    if not klucz:
        return "brak danych"
    return mapa.get(str(klucz).lower(), str(klucz))
