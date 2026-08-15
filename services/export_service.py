"""
EXPORT SERVICE - Eksport danych do CSV i Excel

Zamienia DataFrame na bajty gotowe do pobrania przyciskiem
st.download_button. Uzywane w kilku zakladkach, wiec trzymamy
to w jednym miejscu.

Uzywane w: views/observed_view.py, views/scanner_view.py, views/portfolio_view.py
"""

import io
from datetime import datetime

import pandas as pd


def do_csv(df):
    """
    Konwertuje DataFrame na bajty CSV (kodowanie przyjazne Excelowi PL).

    :return: bytes
    """
    return df.to_csv(index=False).encode("utf-8-sig")


def do_excel(df, nazwa_arkusza="Dane"):
    """
    Konwertuje DataFrame na bajty pliku XLSX.

    :return: bytes
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=nazwa_arkusza[:31])
    return buffer.getvalue()


def do_excel_wiele(arkusze):
    """
    Zapisuje kilka DataFrame do jednego pliku XLSX (po jednym arkuszu).

    :param arkusze: {"Pozycje": df1, "Transakcje": df2}
    :return: bytes
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nazwa, df in arkusze.items():
            if df is None or len(df) == 0:
                continue
            df.to_excel(writer, index=False, sheet_name=str(nazwa)[:31])
    return buffer.getvalue()


def nazwa_pliku(prefix, rozszerzenie):
    """
    Buduje nazwe pliku ze znacznikiem czasu.

    :return: np. "stock_monitor_20260815_1830.csv"
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{prefix}_{stamp}.{rozszerzenie}"


MIME_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_CSV = "text/csv"
