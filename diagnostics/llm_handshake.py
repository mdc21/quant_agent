import os
import requests
import json
from dotenv import load_dotenv

def test_groq():
    print("\n--- Testing Groq (Llama 3.1 8B) ---")
    load_dotenv()
    key = os.getenv("GROQ_API_KEY")
    print(f"GROQ API Key: {key}")
    if not key:
        print("❌ ERROR: GROQ_API_KEY not found in .env")
        return

    # Pre-flight check for spaces/quotes
    if key.startswith('"') or key.endswith('"') or " " in key:
        print("⚠️ WARNING: Your Groq key in .env might have quotes or spaces. This WILL cause 401 errors.")
        key = key.strip('"').strip()
        print(f"   Cleaned key for this test: ...{key[-8:]}")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": "Fiduciary Check: Respond with 'Handshake Successful'"}],
        "max_tokens": 20,
         "temperature":1,
    "max_completion_tokens":1024,
    "top_p":1,
    "stream":True,
    "stop":None
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        if res.status_code == 200:
            print(f"✅ SUCCESS: {res.json()['choices'][0]['message']['content']}")
        else:
            print(f"❌ FAILURE: {res.text}")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

def test_gemini_sweep():
    print("\n--- Testing Google Gemini (Model Sweep) ---")
    load_dotenv()
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("❌ ERROR: GOOGLE_API_KEY not found in .env")
        return

    variants = [
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-pro"),
        ("v1beta", "gemini-pro"),
    ]

    for ver, model in variants:
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={key}"
        print(f"Trying {ver}/{model}...")
        try:
            payload = {"contents": [{"parts": [{"text": "Respond with 'Success'"}]}]}
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                print(f"   ✅ SUCCESS! Use this URL: {url.split('?')[0]}")
                return
            else:
                print(f"   ❌ {res.status_code}")
        except:
            print(f"   ❌ Connection Failed")

def test_openai():
    print("\n--- Testing OpenAI (GPT-4o) ---")
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env")
        return

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Fiduciary Check: Respond with 'Handshake Successful'"}],
        "max_tokens": 20
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        if res.status_code == 200:
            print(f"✅ SUCCESS: {res.json()['choices'][0]['message']['content']}")
        else:
            print(f"❌ FAILURE: {res.text}")
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")

if __name__ == "__main__":
    print("YourBestPath Fiduciary Engine - LLM Handshake Diagnostic v3.0")
    test_openai()
    test_groq()
    test_gemini_sweep()
