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


def _kolor_score(wartosc):
    """
    Zwraca kolor tla dla wartosci Score (0-100) w skali czerwony -> zielony.

    Wlasna implementacja zamiast Styler.background_gradient, ktore wymaga
    biblioteki matplotlib (zbedne 30 MB zaleznosci w chmurze).

    :param wartosc: liczba 0-100
    :return: string CSS np. "background-color: #a8d8a0"
    """
    if wartosc is None or (isinstance(wartosc, float) and pd.isna(wartosc)):
        return ""
    try:
        v = max(0.0, min(100.0, float(wartosc)))
    except (TypeError, ValueError):
        return ""

    # 0% = czerwony (220,80,70), 50% = zolty (250,220,120), 100% = zielony (110,190,110)
    if v <= 50:
        t = v / 50
        r = int(220 + (250 - 220) * t)
        g = int(80 + (220 - 80) * t)
        b = int(70 + (120 - 70) * t)
    else:
        t = (v - 50) / 50
        r = int(250 + (110 - 250) * t)
        g = int(220 + (190 - 220) * t)
        b = int(120 + (110 - 120) * t)

    # Ciemny tekst na jasnym tle - czytelne w obu motywach Streamlita
    return f"background-color: rgb({r},{g},{b}); color: #111111"


def styluj_tabele(df, kolumna_score="Score"):
    """
    Zwraca ostylowana tabele z kolorowana kolumna Score.

    Uzywane w zakladkach zamiast .background_gradient() - dziala bez matplotlib.

    :param df: DataFrame do wyswietlenia
    :param kolumna_score: nazwa kolumny do pokolorowania
    :return: obiekt Styler gotowy dla st.dataframe()
    """
    styler = df.style.format(precision=2, na_rep="-")
    if kolumna_score in df.columns:
        styler = styler.map(_kolor_score, subset=[kolumna_score])
    return styler


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
