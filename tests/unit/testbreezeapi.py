import os
import urllib.parse
from datetime import datetime, timezone
from dotenv import load_dotenv
from breeze_connect import BreezeConnect

# Load environment variables
load_dotenv()

def generate_safe_login_url():
    # Fetch your key from .env
    api_key = os.getenv("ICICIDIRECT_API_KEY")
    
    if not api_key:
        raise ValueError("ICICIDIRECT_API_KEY not found in .env file.")

    # If the portal key literally starts with %40, we MUST encode the % as %25
    # so that the server receives the literal '%40' after decoding.
    encoded_key = urllib.parse.quote(api_key, safe='')
    
    # Official Breeze API Login URL
    base_url = "https://api.icicidirect.com/apiuser/login"
    final_url = f"{base_url}?api_key={encoded_key}"
    
    return final_url

print(f"Safe Login URL: {generate_safe_login_url()}")

def capture_session_metadata(redirect_url):
    # Parse the token from the URL string
    parsed = urllib.parse.urlparse(redirect_url)
    token = urllib.parse.parse_qs(parsed.query).get('apisession', [None])[0]
    
    if not token:
        print("Error: Could not find 'apisession' in the URL.")
        return None

    # Institutional Metadata for Layer 0 Lineage [cite: 14, 59]
    session_metadata = {
        "session_token": token,
        "initiated_at": datetime.now(timezone.utc).isoformat(),
        "source_api": "icici_breeze_v1",
        "environment": "macbook_pro_m_series",
        "lineage_id": f"SESS_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    }
    
    return session_metadata

def verify_breeze_access(session_token):
    api_key = os.getenv("ICICIDIRECT_API_KEY")
    secret_key = os.getenv("ICICIDIRECT_SECRET_KEY")
    
    print("\n--- Verifying Active API Access ---")
    breeze = BreezeConnect(api_key=api_key)
    
    try:
        # Step 1: Generate Session with the token
        breeze.generate_session(api_secret=secret_key, session_token=session_token)
        print("Success: Session generated and authenticated.")
        
        # Step 2: Test Fetch (Get Customer Details or a Quote)
        # We'll try to get a quote for a common stock to verify data flow
        quote = breeze.get_quotes(stock_code="RELIND",
                                 exchange_code="NSE",
                                 expiry_date="",
                                 product_type="cash",
                                 right="",
                                 strike_price="")
        
        if quote.get("Status") == 200:
            print("Success: Market data fetch confirmed.")
            print(f"Sample Quote (RELIANCE): {quote['Success'][0]['ltp']}")
            return True
        else:
            print(f"Error fetching data: {quote.get('Error')}")
            return False
            
    except Exception as e:
        print(f"Authentication Failed: {e}")
        return False

# --- Execution Flow ---
print(f"Step 1: Use this URL to log in and get your token:\n{generate_safe_login_url()}\n")

# PASTE THE REDIRECT URL HERE after you log in
user_redirect = "https://127.0.0.1/?apisession=55426099" 

if "YOUR_TOKEN_HERE" not in user_redirect:
    metadata = capture_session_metadata(user_redirect)
    if metadata:
        verify_breeze_access(metadata["session_token"])
else:
    print("Next Step: Log in, then paste your redirect URL into the 'user_redirect' variable in this script.")