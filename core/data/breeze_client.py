try:
    from breeze_connect import BreezeConnect
except (ImportError, Exception):
    BreezeConnect = None
from dotenv import load_dotenv

class BreezeClient:
    _instance = None
    _breeze = None
    _current_token = None

    @classmethod
    def get_instance(cls, session_token: str = None):
        if cls._instance is None:
            cls._instance = cls()
        
        # If no token provided but already initialized, return it
        if not session_token and cls._breeze:
            return cls._breeze

        # Support MOCK mode for simulations
        if session_token == "MOCK":
            from unittest.mock import MagicMock
            cls._breeze = MagicMock()
            cls._breeze.get_portfolio_holdings.return_value = {"Status": 200, "Success": []}
            cls._breeze.get_quotes.return_value = {"Status": 200, "Success": [{"ltp": 1000.0}]}
            cls._current_token = "MOCK"
            return cls._breeze

        # Only initialize if the token is new/different
        if session_token and session_token != cls._current_token:
            cls._instance._initialize_session(session_token)
            cls._current_token = session_token
            
        return cls._instance._breeze

    def _initialize_session(self, session_token: str):
        load_dotenv()
        api_key = os.getenv("ICICI_API_KEY") or os.getenv("ICICIDIRECT_API_KEY")
        secret_key = os.getenv("ICICI_SECRET_KEY") or os.getenv("ICICIDIRECT_SECRET_KEY")
        
        if not api_key or not secret_key:
            # Fallback to Mock if credentials missing and we want a simulation
            print("ICICI Credentials missing. Falling back to MOCK mode for simulation.")
            from unittest.mock import MagicMock
            self._breeze = MagicMock()
            self._breeze.get_portfolio_holdings.return_value = {"Status": 200, "Success": []}
            return
            
        self._breeze = BreezeConnect(api_key=api_key)
        self._breeze.generate_session(api_secret=secret_key, session_token=session_token)
        print("Breeze Global Session Initialized.")

    @classmethod
    def fetch_ltp(cls, stock_code: str):
        if cls._breeze is None:
            return None
        try:
            quote = cls._breeze.get_quotes(stock_code=stock_code, exchange_code="NSE", product_type="cash")
            if quote.get("Status") == 200:
                return float(quote['Success'][0]['ltp'])
        except Exception:
            return None
        return None
