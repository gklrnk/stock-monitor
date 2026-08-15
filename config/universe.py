"""
UNIVERSE - Lista wszystkich spolek w aplikacji

Ten plik przechowuje spolki podzielone na grupy:
- UNIVERSE_DEFAULT: obserwowane (analiza dogłebna)
- SCANNER_UNIVERSE_QUICK: szybki skan okazji (~200 spolek)
- SCANNER_UNIVERSE_FULL: pelny skan (~300 spolek)

Aby dodac/usunac spolke - edytuj TYLKO ten plik.
"""

# ========================================
# OBSERWOWANE SPOLKI (do glebokiej analizy)
# ========================================
UNIVERSE_DEFAULT = {
    "GPW": {
        "PKO.WA": "PKO BP",
        "PEO.WA": "Pekao SA",
        "SAN.WA": "Santander Bank Polska",
        "MBK.WA": "mBank",
        "ALR.WA": "Alior Bank",
        "BHW.WA": "Bank Handlowy",
        "PZU.WA": "PZU",
        "XTB.WA": "XTB",
        "VOT.WA": "Votum",
        "GPW.WA": "GPW SA",
        "DNP.WA": "Dino Polska",
        "LPP.WA": "LPP",
        "ALE.WA": "Allegro",
        "EUR.WA": "Eurocash",
        "PCO.WA": "Pepco Group",
        "EAT.WA": "AmRest",
        "KGH.WA": "KGHM",
        "PKN.WA": "Orlen",
        "JSW.WA": "JSW",
        "KTY.WA": "Grupa Kety",
        "BDX.WA": "Budimex",
        "COG.WA": "Cognor",
        "ATC.WA": "Arctic Paper",
        "CDR.WA": "CD Projekt",
        "11B.WA": "11 bit studios",
        "ACP.WA": "Asseco Poland",
        "TXT.WA": "Text LiveChat",
        "CRI.WA": "Creotech",
        "LBW.WA": "Lubawa",
        "SNT.WA": "Synektik",
        "NEU.WA": "Neuca",
        "SLV.WA": "Selvita",
        "RVU.WA": "Ryvu Therapeutics",
        "DOM.WA": "Dom Development",
        "1AT.WA": "Atal",
        "DVL.WA": "Develia",
        "CAR.WA": "Inter Cars",
        "APR.WA": "Auto Partner",
        "BFT.WA": "Benefit Systems",
    },
    "GLOBAL": {
        "NVDA": "NVIDIA",
        "MSFT": "Microsoft",
        "GOOGL": "Alphabet",
        "AMZN": "Amazon",
        "ASML": "ASML",
        "TSM": "TSMC",
        "AVGO": "Broadcom",
        "AMD": "AMD",
        "LMT": "Lockheed Martin",
        "RHM.DE": "Rheinmetall",
        "BA.L": "BAE Systems",
        "NOC": "Northrop Grumman",
        "MC.PA": "LVMH",
        "RMS.PA": "Hermes",
        "RACE": "Ferrari",
        "COST": "Costco",
        "PEP": "PepsiCo",
        "XOM": "ExxonMobil",
        "RIO": "Rio Tinto",
        "CCJ": "Cameco",
        "BHP": "BHP Group",
        "FCX": "Freeport-McMoRan",
        "LLY": "Eli Lilly",
        "NVO": "Novo Nordisk",
        "UNH": "UnitedHealth",
        "ISRG": "Intuitive Surgical",
        "TMO": "Thermo Fisher",
        "JPM": "JPMorgan Chase",
        "BRK-B": "Berkshire Hathaway",
        "V": "Visa",
        "MA": "Mastercard",
        "BLK": "BlackRock",
        "TSLA": "Tesla",
        "TM": "Toyota",
        "UBER": "Uber",
        "PLTR": "Palantir",
        "CRWD": "CrowdStrike",
        "WM": "Waste Management",
        "ABNB": "Airbnb",
    },
    "MOJE": {}  # Puste - tu trafiaja spolki dodane przez uzytkownika
}


# ========================================
# SKANER OKAZJI - SZYBKI (~200 spolek)
# ========================================
SCANNER_UNIVERSE_QUICK = {
    "GPW": [
        "PKO.WA","PEO.WA","SAN.WA","MBK.WA","ALR.WA","BHW.WA","PZU.WA","XTB.WA","GPW.WA",
        "DNP.WA","LPP.WA","ALE.WA","EUR.WA","PCO.WA","EAT.WA","KGH.WA","PKN.WA","JSW.WA",
        "KTY.WA","BDX.WA","COG.WA","ATC.WA","CDR.WA","11B.WA","ACP.WA","TXT.WA","CRI.WA",
        "LBW.WA","SNT.WA","NEU.WA","SLV.WA","RVU.WA","DOM.WA","1AT.WA","DVL.WA","CAR.WA",
        "APR.WA","BFT.WA","VOT.WA","OPL.WA","TPE.WA","PGE.WA","ENA.WA","CPS.WA",
        "MRC.WA","FTE.WA","PLW.WA","TEN.WA","BOS.WA","MIL.WA","ING.WA","HDR.WA",
        "VRC.WA","PEP.WA","GRN.WA","ATT.WA","AMB.WA",
    ],
    "USA": [
        "AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V","MA","UNH",
        "XOM","JNJ","LLY","AVGO","WMT","PG","HD","CVX","ABBV","BAC","KO","PFE","PEP",
        "TMO","COST","MRK","CSCO","ADBE","MCD","ACN","NFLX","AMD","LIN","DHR","TXN","VZ",
        "WFC","NEE","BMY","PM","RTX","QCOM","HON","LOW","UPS","ORCL","IBM","INTC","T",
        "GS","BLK","AXP","CAT","BA","DIS","GE","MMM","F","GM",
    ],
    "EUROPA": [
        "ASML","MC.PA","RMS.PA","OR.PA","SAP.DE","SIE.DE","NOVN.SW","NESN.SW",
        "AZN.L","SHEL.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","BATS.L","LSEG.L",
        "BA.L","RHM.DE","AIR.PA","SU.PA","BN.PA","DTE.DE","BMW.DE","MBG.DE","VOW3.DE",
        "ALV.DE","BAS.DE","BAYN.DE","IFX.DE","LIN.DE","MUV2.DE","SAN.PA","TTE.PA",
        "ENGI.PA","STLAM.MI","ISP.MI","ENI.MI","G.MI","UCG.MI","INGA.AS","PHIA.AS",
        "PRX.AS","ADYEN.AS","HEIA.AS","ITX.MC","BBVA.MC","SAN.MC","IBE.MC","REP.MC",
    ]
}


# ========================================
# SKANER OKAZJI - PELNY (~300 spolek)
# ========================================
SCANNER_UNIVERSE_FULL = {
    "GPW": SCANNER_UNIVERSE_QUICK["GPW"] + [
        "MBR.WA","STP.WA","KRU.WA","DAT.WA","MAB.WA","VRG.WA","APT.WA",
        "PKP.WA","BIO.WA","MOL.WA","ECH.WA","ATR.WA","GTC.WA","BMC.WA","ACG.WA",
        "SGN.WA","AWM.WA","BRS.WA","OND.WA","LWB.WA","RBW.WA","INK.WA",
        "PXM.WA","MCI.WA","MEX.WA","MDI.WA","ATG.WA","ACT.WA",
    ],
    "USA": SCANNER_UNIVERSE_QUICK["USA"] + [
        "CRM","INTU","AMGN","AMAT","MDLZ","GILD","ADI","BKNG","SBUX","VRTX",
        "MU","ADP","REGN","LRCX","SYK","TJX","MO","CI","BSX","ETN","SO","ZTS",
        "ITW","SLB","EOG","CB","APD","EQIX","NOC","AON","BDX","CME","ICE","FDX",
        "TGT","SHW","DUK","MAR","EMR","PNC","CSX","MPC","SNPS",
        "PANW","NOW","MRVL","FTNT","SNOW","ZM","XYZ","SHOP","PYPL","ROKU",
        "DASH","COIN","LCID","RIVN","LYFT","TWLO","DDOG",
    ],
    "EUROPA": SCANNER_UNIVERSE_QUICK["EUROPA"] + [
        "VNA.DE","DHL.DE","DBK.DE","CBK.DE","LHA.DE","RWE.DE","MRK.DE","HEN3.DE","BEI.DE",
        "SHL.DE","EOAN.DE","AFX.DE","FRE.DE","MTX.DE","SY1.DE","VOD.L","LLOY.L",
        "BARC.L","NWG.L","STAN.L","PRU.L","AV.L","LGEN.L","TSCO.L","SBRY.L","MKS.L",
        "NG.L","SSE.L","CNA.L","BT-A.L","EZJ.L","IAG.L","RR.L","BAB.L","VIV.PA",
        "SGO.PA","CAP.PA","ORA.PA","STMPA.PA","DSY.PA","ML.PA","EL.PA","KER.PA","ACA.PA",
        "GLE.PA","BNP.PA","AI.PA","MT.AS","AKZA.AS","WKL.AS","ASM.AS","BESI.AS",
    ]
}
