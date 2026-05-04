import os
import requests
from dotenv import load_dotenv
from alpha_vantage.timeseries import TimeSeries
from breeze_connect import BreezeConnect

# Load environment variables from .env
load_dotenv()

def test_alpha_vantage():
    print("\n--- Testing Alpha Vantage Connectivity ---")
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("Error: ALPHA_VANTAGE_API_KEY not found in .env")
        return

    try:
        ts = TimeSeries(key=api_key, output_format='pandas')
        data, meta_data = ts.get_quote_endpoint(symbol='IBM')
        print("Success: Alpha Vantage data fetched successfully.")
        print("Latest Quote for IBM:")
        print(data)
    except Exception as e:
        print(f"Error testing Alpha Vantage: {e}")

def test_breeze_connectivity():
    print("\n--- Testing ICICIDIRECT Breeze Connectivity ---")
    api_key = os.getenv("ICICIDIRECT_API_KEY")
    secret_key = os.getenv("ICICIDIRECT_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("Error: ICICIDIRECT credentials not found in .env")
        return

    # Initialize Breeze
    breeze = BreezeConnect(api_key=api_key)
    
    # Note: ICICIDIRECT usually requires a session token generated via a login URL.
    # For a first-time check, we just check if we can initialize the object.
    # To actually fetch data, you need to run: breeze.generate_session(api_secret=secret_key, session_token="YOUR_SESSION_TOKEN")
    
    print(f"Breeze SDK initialized with API Key: {api_key[:5]}...")
    print("To fully verify, you must provide a session token from the Breeze login URL.")
    print(f"Login URL: https://directlink.icicidirect.com/MemberToken.aspx?AppKey={api_key}")
    
    # Check if we can reach the API (using a simple requests call to the version endpoint if it exists)
    try:
        # This is a dummy call just to check network reachability to the API domain
        response = requests.get("https://api.icicidirect.com/breezeapi/v1/", timeout=5)
        if response.status_code in [200, 401, 403]: # 401/403 means we reached the server but lack auth
            print("Success: ICICIDIRECT API server is reachable.")
        else:
            print(f"Warning: Unexpected response from ICICIDIRECT: {response.status_code}")
    except Exception as e:
        print(f"Error reaching ICICIDIRECT API: {e}")

if __name__ == "__main__":
    # Ensure dependencies are installed: pip install -r requirements.txt
    test_alpha_vantage()
    test_breeze_connectivity()
