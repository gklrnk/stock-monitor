"""
CHART SERVICE - Budowanie wykresow (Plotly)

Ten modul odpowiada WYLACZNIE za tworzenie obiektow wykresow.
Widoki (views/) tylko je wyswietlaja przez st.plotly_chart().

Dzieki temu wyglad wykresow zmieniamy w jednym miejscu.

Uzywane w: views/observed_view.py, views/basket_view.py, views/portfolio_view.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.formatting import KOLORY_SYGNALOW


def wykres_techniczny(hist, nazwa, target=None):
    """
    Buduje 4-panelowy wykres techniczny: swiece + SMA, wolumen, RSI, MACD.

    :param hist: DataFrame z Yahoo (kolumny Open/High/Low/Close/Volume)
    :param nazwa: nazwa spolki do tytulu
    :param target: opcjonalna cena docelowa analitykow
    :return: obiekt Figure
    """
    close = hist["Close"].squeeze()

    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()

    e12 = close.ewm(span=12).mean()
    e26 = close.ewm(span=26).mean()
    macd_l = e12 - e26
    signal_l = macd_l.ewm(span=9).mean()
    macd_h = macd_l - signal_l

    delta = close.diff()
    zysk = delta.where(delta > 0, 0.0)
    strata = -delta.where(delta < 0, 0.0)
    rs = zysk.rolling(14).mean() / strata.rolling(14).mean()
    rsi_s = 100 - (100 / (1 + rs))

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.45, 0.15, 0.20, 0.20],
        vertical_spacing=0.02,
        subplot_titles=[f"{nazwa} - Cena + SMA", "Wolumen", "RSI", "MACD"],
    )

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name="Cena"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=sma20, name="SMA20",
                             line=dict(color="blue", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=sma50, name="SMA50",
                             line=dict(color="orange", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=sma200, name="SMA200",
                             line=dict(color="red", width=2)), row=1, col=1)

    if target:
        try:
            fig.add_hline(y=float(target), line_dash="dash", line_color="purple",
                          annotation_text=f"Cel analitykow: {round(float(target), 2)}",
                          row=1, col=1)
        except (TypeError, ValueError):
            pass

    kolory_wol = ["green" if float(c) >= float(o) else "red"
                  for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Wolumen",
                         marker_color=kolory_wol), row=2, col=1)

    fig.add_trace(go.Scatter(x=hist.index, y=rsi_s, name="RSI",
                             line=dict(color="purple")), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.add_trace(go.Scatter(x=hist.index, y=macd_l, name="MACD",
                             line=dict(color="blue")), row=4, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=signal_l, name="Signal",
                             line=dict(color="orange")), row=4, col=1)
    kolory_macd = ["green" if float(v) >= 0 else "red" for v in macd_h.fillna(0)]
    fig.add_trace(go.Bar(x=hist.index, y=macd_h, name="Histogram",
                         marker_color=kolory_macd), row=4, col=1)

    fig.update_layout(height=900, showlegend=False, xaxis_rangeslider_visible=False)
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    return fig


def wykres_top_score(df, ile=20):
    """Slupkowy wykres TOP spolek wg Score."""
    return px.bar(
        df.head(ile), x="Ticker", y="Score", color="SYGNAL",
        hover_data=["Nazwa", "Cena", "1M%", "PE"],
        title=f"TOP {ile} spolek wg Score",
        color_discrete_map=KOLORY_SYGNALOW, height=450,
    )


def wykres_momentum_score(df):
    """Scatter: momentum 1M vs Score."""
    fig = px.scatter(
        df, x="1M%", y="Score", color="Rynek", size="Score",
        hover_name="Nazwa", title="Momentum (1M) vs Score", height=400,
    )
    fig.add_hline(y=55, line_dash="dash", line_color="green")
    fig.add_hline(y=70, line_dash="dash", line_color="darkgreen")
    return fig


def wykres_rozklad_sygnalow(df):
    """Kolowy wykres rozkladu sygnalow."""
    counts = df["SYGNAL"].value_counts()
    return px.pie(
        names=counts.index, values=counts.values,
        title="Rozklad sygnalow", color=counts.index,
        color_discrete_map=KOLORY_SYGNALOW, height=400,
    )


def wykres_porownanie_cen(dane_cen):
    """
    Porownanie znormalizowanych cen kilku spolek (start = 100).

    :param dane_cen: {"NVDA": Series, "CDR.WA": Series}
    """
    fig = go.Figure()
    for ticker, seria in dane_cen.items():
        if seria is None or len(seria) == 0:
            continue
        baza = float(seria.iloc[0])
        if baza == 0:
            continue
        znorm = (seria / baza) * 100
        fig.add_trace(go.Scatter(x=seria.index, y=znorm, name=ticker, mode="lines"))
    fig.add_hline(y=100, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Porownanie stop zwrotu (start = 100)",
        height=450, yaxis_title="Indeks (start = 100)",
    )
    return fig


def wykres_struktura_portfela(pozycje):
    """
    Kolowy wykres udzialu pozycji w portfelu wg wartosci aktualnej.

    :param pozycje: lista pozycji z pobierz_pozycje_z_wycena()
    """
    dane = [p for p in pozycje if p.get("wartosc_aktualna")]
    if not dane:
        return None
    df = pd.DataFrame([{
        "Ticker": p["ticker"],
        "Wartosc": p["wartosc_aktualna"],
    } for p in dane])
    return px.pie(df, names="Ticker", values="Wartosc",
                  title="Struktura portfela (wartosc aktualna)", height=400)


def wykres_zysk_pozycji(pozycje):
    """Slupkowy wykres zysku procentowego dla otwartych pozycji."""
    dane = [p for p in pozycje if p.get("zysk_pct") is not None]
    if not dane:
        return None
    df = pd.DataFrame([{
        "Ticker": p["ticker"],
        "Zysk %": p["zysk_pct"],
    } for p in dane]).sort_values("Zysk %", ascending=False)
    fig = px.bar(df, x="Ticker", y="Zysk %", color="Zysk %",
                 color_continuous_scale="RdYlGn",
                 title="Zysk / strata otwartych pozycji (%)", height=400)
    fig.add_hline(y=0, line_color="black")
    return fig
