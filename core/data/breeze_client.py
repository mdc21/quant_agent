import os
from breeze_connect import BreezeConnect
from dotenv import load_dotenv

class BreezeClient:
    _instance = None
    _breeze = None
    _current_token = None

    @classmethod
    def get_instance(cls, session_token: str = None):
        if cls._instance is None:
            cls._instance = cls()
        
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
            raise ValueError(f"ICICI Credentials missing in .env (Checked ICICI_API_KEY and ICICIDIRECT_API_KEY)")
            
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
