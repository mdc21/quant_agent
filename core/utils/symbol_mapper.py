from typing import Dict
from functools import lru_cache

class SymbolMapper:
    """
    Utility to map NSE symbols to ICICI Breeze Stock Codes.
    """
    
    # Common Nifty constituent mismatches [cite: 59]
    _NSE_TO_BREEZE = {
        "RELIANCE": "RELIND",
        "HDFCBANK": "HDFBAN",
        "ICICIBANK": "ICIBAN",
        "BAJAJFINSV": "BAJFNS",
        "BAJFINANCE": "BAJFI",
        "KOTAKBANK": "KOTMAH",
        "NATIONALUM": "NATALU",
        "M&M": "MAHMAH",
        "L&T": "LANTUF",
        "HCLTECH": "HCLTEC",
        "SUNPHARMA": "SUNPHA",
        "DRREDDY": "DRREDD",
        "BHARTIARTL": "BHAART",
        "ADANIPORTS": "ADAPOR",
        "ADANIENT": "ADAENT",
        "COALINDIA": "COALIN",
        "JSWSTEEL": "JSWSTE",
        "TATASTEEL": "TATSTE",
        "POWERGRID": "POWGRI",
        "TITAN": "TITAN",
        "ULTRACEMCO": "ULTCEM",
        "NTPC": "NTPC",
        "ITC": "ITC",
        "ASIANPAINT": "ASIPAI",
        "HINDALCO": "HINDAL",
        "SBIN": "SBIN",
        "HINDUNILVR": "HINLEV",
        "INFY": "INFTEC",
        "TCS": "TCS",
        "AXISBANK": "AXIBAN",
        "MARUTI": "MARUTI",
        "INDUSINDBK": "INDBAN",
        "BAJAJ-AUTO": "BAAUTO",
        "WIPRO": "WIPRO",
        "APOLLOHOSP": "APOHOS",
        "EICHERMOT": "EICMOT",
        "HEROMOTOCO": "HERHON",
        "BPCL": "BPCL",
        "ONGC": "ONGC",
        "ADANIPOWER": "ADAPOW",
        "TATAELXSI": "TATAEL",
        "POLYCAB": "POLYCAB",
        "PATANJALI": "PATANJ",
        "SHREECEM": "SHRCEM",
        "CHOLAFIN": "CHOFIN",
        "MOTHERSON": "SAMMOT",
        "GAIL": "GAIL",
        "MFSL": "MAXFIN",
        "DEEPAKFERT": "DEEFER",
        "BAJAJHLDNG": "BAJHLD",
        "HDFCAMC": "HDFAMC",
        "IDBI": "IDBIBANK",
        "FORCEMOT": "FORMOT",
        "FORTIS": "FORHEA",
        "FIVESTAR": "FIVEST",
        "OIL": "OILIND",
        "ITI": "ITI",
        "PIRAMALFIN": "PIRENT",
        "PPLPHARMA": "PPLPHA",
        "SIEMENS": "SIEMEN",
        "IRCTC": "IRCTC",
        "LTF": "L&TFH",
        "HYUNDAI": "HYUNDA",
        "EXIDEIND": "EXIIND",
        "ANGELONE": "ANGELONE",
        "COFORGE": "NIITEC",
        "TATACONSUM": "TATGLO",
        "ASTERDM": "ASTHEA",
        "INDHOTEL": "INDHOT",
        "BANDHANBNK": "BANBNK",
        "JBMA": "JBMA",
        "HINDZINC": "HINZIN",
        "DATAPATTNS": "DATPAT",
        "KPITTECH": "KPITEC",
        "RECLTD": "RECLTD",
        "FEDERALBNK": "FEDBNK",
        "BRIGADE": "BRIENT",
        "SWANCORP": "SWANEN",
        "DLF": "DLF",
        "LAURUSLABS": "LAULAB",
        "JIOFIN": "JIOFIN",
        "NESTLEIND": "NESIND",
        "AARTIIND": "AARIND",
        "LICHSGFIN": "LICHFL",
        "KALYANKJIL": "KALKJU",
        "HBLENGINE": "HBLPOW",
        "GODREJCP": "GODCP",
        "ICICIGI": "ICIGEN",
        "MANAPPURAM": "MANFIN",
        "UPL": "UPL",
        "VOLTAS": "VOLTAS",
        "FSL": "FSL",
        "GMDCLTD": "GUJMIN",
        "MUTHOOTFIN": "MUTFIN",
        "IFCI": "IFCI",
        "BLS": "BLS",
        "TORNTPHARM": "TORPHA",
        "CDSL": "CDSL",
        "INOXWIND": "INOWIN",
        "SUPREMEIND": "SUPIND",
        "ABCAPITAL": "ADBCAP",
        "NMDC": "NMDC",
        "AUROPHARMA": "AURPHA",
        "CGCL": "CAPGCO",
        "BOSCHLTD": "BOSCH",
        "WAAREEENER": "WAAREE",
        "RVNL": "RVNL",
        "AMBUJACEM": "AMBCEM",
        "OFSS": "ORAFIN",
        "ALKEM": "ALKLAB",
        "TATAPOWER": "TATPOW",
        "GVT&D": "GEP&D",
        "DELHIVERY": "DELHIV",
        "AUBANK": "AUBANK",
        "MOTILALOFS": "MOTWAL",
        "NYKAA": "FSNONT",
        "ZYDUSLIFE": "ZYDLIF",
        "JUBLFOOD": "JUBFOO",
        "BHARATFORG": "BHAFOR",
        "GODREJPROP": "GODPRO",
        "NEULANDLAB": "NEULAB",
        "GLAND": "GLAPHA",
        "MAZDOCK": "MAZDOCK",
        "TMCV": "TATMOT",
        "NH": "NARHRU",
        "DEVYANI": "DEVINT",
        "SYNGENE": "SYNGEN",
        "CANBK": "CANBAN",
        "BHARAT22ETF": "BHA22",
        "ICICINXT50": "ICINEX",
        "ICICIGOLD": "ICIGOL",
        "CPSEETF": "CPSETF",
        "NIFTYBEES": "NIFBEE",
        "ICICINIFTY": "ICIN30",
        "CESC": "CESC",
        "INDIANB": "INDIANB",
        "LALPATHLAB": "DRLAL",
        "PIDILITIND": "PIDIND",
        "TVSMOTOR": "TVSMOT",
        "WELCORP": "WELGUJ",
        "BAJAJFINSV": "BAJFNS",
        "OLAELEC": "OLAELE",
        "KEI": "KEIIND",
        "NUVAMA": "NUVAMA",
        "BANKINDIA": "BANIND",
        "SWIGGY": "SWIGGY",
        "HAVELLS": "HAVELL",
        "AEGISLOG": "AEGLOG",
        "M&MFIN": "MAHFAN",
        "NAVINFLUOR": "NAVFLU",
        "HSCL": "HIMSYS",
        "ICICIAMC": "ICIPRU",
        "PIIND": "PIIND",
        "BSE": "BSE",
        "ABB": "ABB",
        "JINDALSTEL": "JINSTE",
        "LODHA": "MACLOD",
        "COROMANDEL": "CORINT",
        "CHOLAHLDNG": "CHOHLD",
        "BIOCON": "BIOCON",
        "COHANCE": "SOLPHA",
        "SONACOMS": "SONCOM",
        "NHPC": "NHPC",
        "GLENMARK": "GLEPHA",
        "PAYTM": "ONE97",
        "GRASIM": "GRASIM",
        "BANKBARODA": "BANBAR",
        "SARDAEN": "SARENE",
        "JMFINANCIL": "JMFINA",
        "TATACAP": "TATCAP",
        "UNITDSPR": "UNISPI",
        "RBLBANK": "RBLBAN",
        "IKS": "IKSSOL",
        "STARHEALTH": "STAHEA",
        "INDIGO": "INTERA",
        "PWL": "POWGRI",
        "PGEL": "PGELEC",
        "HUDCO": "HUDCO",
        "ANANDRATHI": "ANARAT",
        "PRESTIGE": "PREEST",
        "IIFL": "IIFL",
        "ETERNAL": "ETERNAL",
        "ANANTRAJ": "ANARAJ",
        "MPHASIS": "MPHASI",
        "MEESHO": "MEESHO",
        "POONAWALLA": "POONAW",
        "BEL": "BEL",
        "TATACOMM": "TATCOM",
        "SHRIRAMFIN": "SHRUTI",
        "REDINGTON": "REDING",
        "JSWENERGY": "JSWENE",
        "JYOTICNC": "JYOCNC",
        "ABREL": "ADAREN",
        "LT": "LARTOU",
        "HAL": "HINAER",
        "FEDERALBNK": "FEDBAN",
        "BHARTIARTL": "BHAAIR",
        "TECHM": "TECMAH",
        "TITAN": "TITIND",
        "IDFCFIRSTBK": "IDFBAN",
        "ASHOKLEY": "ASHLEY",
        "JKPAPER": "JKPAP",
        "ADANIWILMAR": "ADAWIL",
        "HAPPSTMNDS": "HAPMIN",
        "TATASTEEL": "TATSTE",
        "TATAELXSI": "TATAEL",
        "BAJAJFINSV": "BAFINS",
        "TATAMOTORS": "TATMOT",
        "TCS": "TCS",
        "WIPRO": "WIPRO",
        "INFY": "INFY",
        "RELIANCE": "RELIANCE",
        "HDFCBANK": "HDFCBANK",
        "ICICIBANK": "ICICIBANK",
        "SBIN": "STABAN",
        "AXISBANK": "AXISBANK",
        "KOTAKBANK": "KOTAKBANK",
        "HINDUNILVR": "HINDUNILVR",
        "BIOCON": "BIOCON",
        "STARHEALTH": "STARHEALTH",
        "GAIL": "GAIL",
        "ONGC": "ONGC",
        "POWERGRID": "POWERGRID",
        "GRASIM": "GRASIM",
        "MCX": "MCX",
        "PERSISTENT": "PERSYS",
        "ADANIWILMAR": "ADAWIL",
        "HINDUNILVR": "HINLEV",
        "KOTAKBANK": "KOTMAH",
        "HCLTECH": "HCLTEC",
        "HDFCBANK": "HDFBAN",
        "AXISBANK": "AXIBAN",
        "ICICIBANK": "ICIBAN",
        "RELIANCE": "RELIND",
        "INFY": "INFTEC",
        "TATACOMM": "TATCOM",
        "CHOLAFIN": "CHOINV",
        "STARHEALTH": "STAHEA",
        "ADANIPORTS": "ADAPOR",
        "ADANIENT": "ADAENT",
        "M&M": "MAHMAH",
        "BAJFINANCE": "BAJFI",
        "BAJAJFINSV": "BAJFNS",
        "TATASTEEL": "TATSTE",
        "TATAMOTORS": "TATMOT",
        "TATAPOWER": "TATPOW",
        "L&T": "LANTUF",
        "HAL": "HINAER",
        "FEDERALBNK": "FEDBAN",
        "TECHM": "TECMAH",
        "TITAN": "TITIND",
        "IDFCFIRSTBK": "IDFBAN",
        "ASHOKLEY": "ASHLEY",
        "JKPAPER": "JKPAP",
        "HAPPSTMNDS": "HAPMIN",
        "LICHSGFIN": "LICHFL",
        "ICICINIFTY": "ICIN30",
        "ICICINXT50": "ICINEX",
        "BHARAT22ETF": "BHA22",
        "NIFTYBEES": "NIFBEE",
        "CPSEETF": "CPSETF",
        "ICICIGOLD": "ICIGOL",
        "MEG": "MEGINF",
        "EON": "EONELE",
        "SHALPAINTS": "SHALIM",
        "HEIDELBERG": "HEICEM",
        "IEX": "INDEN",
        "LICI": "LIC",
        "MARICO": "MARLIM",
        "ADAREN": "ABREL",
        # ── Confirmed ICICI Direct → NSE mappings (2026 official table) ──
        # Direction: NSE_symbol → Breeze_code (reverse scan in to_nse finds Breeze→NSE)
        "MOTILALC10": "MORSTA",   # Motilal Oswal Nifty Capital Markets ETF
        "INDUSTOWER": "BHAINF",   # Indus Towers Limited
        "RELCOM":     "RELCON",   # Reliance Communications
        "MIDCAPIETF": "REL150",   # ICICI Pru Nifty Midcap 150 ETF
        "LGEINDIA":   "LGELEC",   # LG Electronics India
        "MAJLIM":     "EMULIM",   # Majesco Limited
        "GLAXO":      "GLACON",   # GlaxoSmithKline Consumer
        "TMCV":       "TATCOV",   # Tata Motors Commercial Vehicles
        "GOLDIETF":   "GOLDEX",   # ICICI Prudential Gold ETF
        "AMTL":       "ADVMET",   # Advance Metering Technology Ltd
    }

    # Standard NSE to Yahoo Ticker overrides (where they differ)
    _NSE_TO_YAHOO = {
        # ── ETF / Index Fund Breeze codes ──────────────────────────────
        "ADANIWILMAR":  "AWL",
        "IDFCFIRSTBK":  "IDFCFIRSTB",
        "BHARAT22ETF":  "ICICIB22",
        "NIFTYBEES":    "NIFTYBEES",
        "ICICINIFTY":   "ICICINIFTY",
        "ICICINXT50":   "ICICINXT50",
        "CPSEETF":      "CPSEETF",
        "ICICIGOLD":    "ICICIGOLD",
        "ICICIHEAL":    "ICICIHEAL",        # ICICI Pru Healthcare ETF
        "SBIN50":       "SETFNIF50",        # SBI ETF Nifty 50
        "ICI100":       "ICICIN100",        # ICICI Nifty 100 ETF
        "ICI150":       "ICICINXT50",       # Best proxy: ICICI Nifty Next 50
        "ICI500":       "ICICIB22",         # Broad index proxy
        "ICIN20":       "ICICINIFTY",       # ICICI Nifty 200 → Nifty proxy
        "ICINIF":       "ICICINIFTY",       # ICICI Nifty fund
        "MIRNYS":       "MAFANG",           # Mirae Asset NYSE FANG+ ETF
        # ── Stock codes: Breeze short → correct Yahoo/NSE ticker ───────
        "ICILOM":       "ICICIGI",          # ICICI Lombard GIC (correct NSE/Yahoo)
        "ICILOMBARD":   "ICICIGI",          # alt code
        "ICICILOMBARD": "ICICIGI",          # alt code
        "SBILIF":       "SBILIFE",          # SBI Life Insurance
        "GIC":          "GICRE",            # GIC Re
        "TATTEC":       "TATATECH",         # Tata Technologies
        "DCB":          "DCBBANK",          # DCB Bank
        "MEG":          "MEGHMANIFN",       # Meghmani Finechem
        "MEGINF":       "MEGHMANIFN",       # Meghmani Finechem (alt code)
        "EON":          "EONELECTRIC",      # EON Electric
        "EONELE":       "EONELECTRIC",      # EON Electric (alt code)
        "ITCHOT":       "ITCHOTELS",        # ITC Hotels
        "NIVBUP":       "NIVABUPA",         # Niva Bupa Health Insurance
        "ICIHEA":       "ICICIHEAL",        # ICICI Healthcare ETF
        "INDMAR":       "INDIAMART",        # IndiaMART InterMESH
        "CAPPOI":       "CAPLIPOINT",       # Caplin Point Laboratories
        "BAFINS":       "BAJAJFINSV",       # Bajaj Finserv
        "JKLAKS":       "JKLAKSHMI",        # JK Lakshmi Cement
        "AFFIND":       "AFFLE",            # Affle India
        "HDFSTA":       "HDFCLIFE",         # HDFC Life Insurance
        "GLOHEA":       "MEDANTA",          # Global Health (Medanta)
        "ADICAP":       "ABCAPITAL",        # Aditya Birla Capital
        "ABBPOW":       "ABB",              # ABB Power Products & Systems
        # ── ICICI ETF codes: NSE tickers with no Yahoo data → use liquid proxies ──
        "ICICINIFTY":   "NIFTYBEES",        # ICICI Nifty 50 ETF → Nippon Nifty proxy
        "ICICIN100":    "NIFTYBEES",        # ICICI Nifty 100 ETF → Nifty proxy
        "ICICINXT50":   "JUNIORBEES",       # ICICI Nifty Next 50 ETF → Junior Bees proxy
        "ICICIGOLD":    "GOLDBEES",         # ICICI Gold ETF → Gold Bees proxy
        "MIDCAPIETF":   "MID150BEES",       # ICICI Midcap 150 ETF proxy
        "GOLDIETF":     "GOLDBEES",         # ICICI Gold ETF (alt code)
        "MOTILALC10":   "NIFTYBEES",        # Motilal Oswal Capital Markets ETF → Nifty proxy
        # ── Small-cap stocks with limited Yahoo coverage → use as-is, fallback to cost ──
        "MEGHMANIFN":   "MEGHMANIFN",       # Meghmani Finechem (Yahoo may lack data)
        "EONELECTRIC":  "EONELECTRIC",      # EON Electric (Yahoo may lack data)
    }

    # ── Instruments with confirmed ₹0 market value ──────────────────────────
    # These are bankrupt, delisted, or wound-up. Using cost price OVERSTATES value.
    # Valuation loop should assign market_value = 0, not avg_buy_price.
    _KNOWN_ZERO_VALUE = frozenset({
        "RELCOM",    # Reliance Communications — NCLT bankruptcy proceedings
        "MAJLIM",    # Majesco — delisted after promoter buyback (₹0 on market)
        "GLAXO",     # GSK Consumer — delisted; shares converted to HUL at close
    })

    # ── Tickers with no Yahoo coverage but still economically live ───────────
    # to_nse() maps these correctly; yfinance returns empty; fallback = avg_buy_price.
    _KNOWN_UNRESOLVABLE = frozenset({
        "LGEINDIA",     # LG Electronics India — private subsidiary, no listing
        "AMTL",         # Advance Metering Technology — limited coverage
        "MEGHMANIFN",   # Meghmani Finechem — limited Yahoo coverage
        "EONELECTRIC",  # EON Electric — limited Yahoo coverage
        "ICICIHEAL",    # ICICI Healthcare ETF — covered via NIFTYBEES proxy above
        # INDUSTOWER removed — actively traded on NSE, Yahoo has full data
    })

    @classmethod
    @lru_cache(maxsize=1024)
    def is_zero_value(cls, symbol: str) -> bool:
        """Returns True for bankrupt/delisted instruments whose market value is ₹0."""
        nse = cls.to_nse(symbol.strip().lstrip('$'))
        return nse in cls._KNOWN_ZERO_VALUE

    @classmethod
    @lru_cache(maxsize=1024)
    def is_resolvable(cls, symbol: str) -> bool:
        """Returns False for instruments with no Yahoo data (but still economically live).
        Note: zero-value instruments ARE 'resolvable' — we just resolve them to ₹0."""
        nse = cls.to_nse(symbol.strip().lstrip('$'))
        return nse not in cls._KNOWN_UNRESOLVABLE and nse not in cls._KNOWN_ZERO_VALUE

    @classmethod
    @lru_cache(maxsize=1024)
    def to_yahoo(cls, symbol: str) -> str:
        """Converts NSE Symbol or Breeze Code to a valid Yahoo Ticker (without .NS)."""
        # First, ensure we have the standard NSE Ticker
        nse = cls.to_nse(symbol)
        # Then check for Yahoo-specific overrides
        return cls._NSE_TO_YAHOO.get(nse, nse)

    @classmethod
    @lru_cache(maxsize=1024)
    def to_breeze(cls, nse_symbol: str) -> str:
        """Converts NSE Symbol to Breeze Stock Code."""
        # Check explicit mapping first
        if nse_symbol in cls._NSE_TO_BREEZE:
            return cls._NSE_TO_BREEZE[nse_symbol]
        
        # Heuristic for symbols with &
        if "&" in nse_symbol:
            # Breeze often uses 'P&D' -> 'P&D' or replaces with '_'
            # But the specific GE T&D case is GEP&D
            return nse_symbol 
            
        return nse_symbol

    @classmethod
    @lru_cache(maxsize=1024)
    def to_nse(cls, breeze_code: str) -> str:
        """Converts Breeze Stock Code back to NSE Symbol (Reverse lookup)."""
        for nse, breeze in cls._NSE_TO_BREEZE.items():
            if breeze == breeze_code:
                return nse
        return breeze_code

    @classmethod
    @lru_cache(maxsize=1024)
    def get_sector(cls, symbol: str) -> str:
        """Returns the industry sector for a given symbol."""
        # Normalize to NSE ticker
        nse = cls.to_nse(symbol.strip().lstrip('$'))
        
        # Comprehensive mapping for top 100 constituents
        _SECTORS = {
            # Technology
            "TCS": "Technology", "INFY": "Technology", "WIPRO": "Technology", 
            "HCLTECH": "Technology", "TECHM": "Technology", "LTIM": "Technology",
            "COFORGE": "Technology", "MPHASIS": "Technology", "PERSISTENT": "Technology",
            "KPITTECH": "Technology", "TATAELXSI": "Technology",
            
            # Financial Services / Banking
            "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", 
            "SBIN": "Financial Services", "AXISBANK": "Financial Services", 
            "KOTAKBANK": "Financial Services", "BAJFINANCE": "Financial Services",
            "BAJAJFINSV": "Financial Services", "CHOLAFIN": "Financial Services",
            "SHRIRAMFIN": "Financial Services", "MUTHOOTFIN": "Financial Services",
            
            # Healthcare
            "SUNPHARMA": "Health Care", "DRREDDY": "Health Care", "CIPLA": "Health Care", 
            "APOLLOHOSP": "Health Care", "TORNTPHARM": "Health Care", "ALKEM": "Health Care",
            "ZYDUSLIFE": "Health Care", "MAXHEALTH": "Health Care", "LALPATHLAB": "Health Care",
            
            # Energy & Utilities
            "RELIANCE": "Energy", "ONGC": "Energy", "BPCL": "Energy", "IOC": "Energy",
            "NTPC": "Utilities", "POWERGRID": "Utilities", "ADANIGREEN": "Utilities",
            "ADANITRANS": "Utilities", "TATAPOWER": "Utilities",
            
            # Consumer Goods / FMCG
            "HINDUNILVR": "Consumer Goods", "ITC": "Consumer Goods", "NESTLEIND": "Consumer Goods", 
            "BRITANNIA": "Consumer Goods", "GODREJCP": "Consumer Goods", "DABUR": "Consumer Goods",
            "VBL": "Consumer Goods", "TATACONSUM": "Consumer Goods",
            
            # Automobile
            "MARUTI": "Automobile", "TATAMOTORS": "Automobile", "M&M": "Automobile", 
            "BAJAJ-AUTO": "Automobile", "EICHERMOT": "Automobile", "TVSMOTOR": "Automobile",
            "HEROMOTOCO": "Automobile", "ASHOKLEY": "Automobile",
            
            # Materials & Metals
            "JSWSTEEL": "Materials", "TATASTEEL": "Materials", "HINDALCO": "Materials",
            "GRASIM": "Materials", "ULTRACEMCO": "Materials", "JINDALSTEL": "Materials",
            "AMBUJACEM": "Materials", "ACC": "Materials",
            
            # Others
            "BHARTIARTL": "Telecommunication", "INDIGO": "Services",
            "ADANIPORTS": "Infrastructure", "L&T": "Construction",
            "TITAN": "Consumer Durables", "ASIANPAINT": "Consumer Durables"
        }
        return _SECTORS.get(nse, None) # Return None if not in hardcoded list to allow fallback
