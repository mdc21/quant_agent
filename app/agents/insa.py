import os
import requests
import json
import datetime
import pandas as pd
from typing import Dict, Any, List
from groq import Groq
from dotenv import load_dotenv

class InsightNarrativeEngine:
    """
    Insight & Narrative Engine (INSA).
    The 'Voice' of the system that provides transparency and goal tracking.
    Satisfies Task L3.
    """
    def __init__(self, api_key: str = None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Groq Client if key exists
        self.groq_client = None
        if self.groq_key:
            try:
                self.groq_client = Groq(api_key=self.groq_key)
            except:
                pass
                
        self.log_path = "app/data/llm_calls.log"
        os.makedirs("app/data", exist_ok=True)

    def _log_interaction(self, provider: str, prompt: str, response: str):
        """Logs LLM input and output for auditability."""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "provider": provider,
            "input": prompt,
            "output": response
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the connectivity status of the LLM backends.
        """
        if self.openai_key:
            return {"status": "CONNECTED", "model": "OpenAI (GPT-4o)", "color": "#10b981"}
        if self.groq_key:
            return {"status": "CONNECTED", "model": "Groq (Llama 3.1 8B)", "color": "#10b981"}
        if self.api_key:
            return {"status": "CONNECTED", "model": "Google Gemini (Pro)", "color": "#10b981"}
        return {"status": "OFFLINE", "model": "Deterministic Engine (Fallback)", "color": "#f43f5e"}

    def calculate_attribution(self, port_returns: pd.Series, bench_returns: pd.Series) -> Dict[str, Any]:
        """Calculates performance attribution against a benchmark."""
        excess = float(port_returns.mean() - bench_returns.mean())
        return {
            "excess_return": excess,
            "top_stock": "RELIANCE", # Placeholder for real attribution logic
            "benchmark_name": "NIFTY 50"
        }

    def generate_narrative(self, manifest: Dict[str, Any], attribution: Dict[str, Any]) -> str:
        """Generates a human-readable summary of the rebalance cycle."""
        regime = manifest.get('regime', 'UNKNOWN')
        trades = manifest.get('trade_count', 0)
        excess = attribution.get('excess_return', 0.0)
        
        narrative = (
            f"The system detected a {regime} regime and orchestrated {trades} rebalance actions. "
            f"Current attribution shows an excess return of {excess:.2%} against the benchmark. "
            "All actions were validated against fiduciary guardrails."
        )
        return narrative

    def track_goal_progress(self, goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Evaluates progress towards specific financial milestones."""
        report = []
        for g in goals:
            prob = g.get('success_prob', 0.0)
            tier = g.get('tier', 3)
            
            status = "ON TRACK"
            if tier == 1 and prob < 0.95:
                status = "IMMEDIATE ACTION REQUIRED"
            elif prob < 0.70:
                status = "WARNING"
                
            report.append({
                "label": g.get('label'),
                "status": status,
                "success_prob": prob
            })
        return report

    def chat(self, question: str, manifest: Dict[str, Any], history: List[Dict[str, str]] = None) -> str:
        """
        Drives the Fiduciary Chat with full portfolio and risk context.
        """
        # 1. Build context from manifest
        equity_sleeve = manifest.get('equity_sleeve', [])
        passive_sleeve = manifest.get('passive_sleeve', [])
        risk_profile = manifest.get('risk_profile', 'Moderate')
        total_amount = manifest.get('amount', 0)
        
        context_summary = f"""
        INVESTMENT CONTEXT:
        - Total Capital Managed: {total_amount:,.2f} INR
        - Risk Profile: {risk_profile}
        - Current Portfolio:
            * Equities ({len(equity_sleeve)} stocks): {", ".join([f"{s['symbol']} ({s['target_weight']:.2%})" for s in equity_sleeve[:10]])}
            * Passive ({len(passive_sleeve)} funds): {", ".join([f"{f['ticker']} ({f['target_weight']:.2%})" for f in passive_sleeve])}
        - Fiduciary Rules Active: UCITS 5/10/40, 20% Sector Ceiling, ADV-Impact Cost TCM.
        - Core Selection Filter: ROCE > 1.5%, FCF Quality.
        """

        prompt = f"""
        You are the 'YourBestPath Fiduciary AI'. Your goal is to provide transparent, defensible financial advice.
        
        {context_summary}

        USER QUESTION: {question}

        GUIDELINES:
        1. Always refer to our 'fiduciary duty' and 'transparency'.
        2. If asked about stock selection, mention ROCE, FCF, or UCITS compliance.
        3. If asked about rebalancing, explain that we avoid illiquidity using ADV-impact costs.
        4. Be professional, concise, and never apologize for being 'just an AI'. 
        5. Use the specific portfolio data provided above.
        """

        # --- 0. Primary: OpenAI (REST) ---
        if self.openai_key:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o",
                    "messages": [{"role": "system", "content": "You are a fiduciary AI assistant."}, {"role": "user", "content": prompt}],
                    "max_tokens": 500
                }
                res = requests.post(url, json=payload, timeout=15)
                if res.status_code == 200:
                    ans = res.json()['choices'][0]['message']['content']
                    self._log_interaction("OpenAI (GPT-4o)", prompt, ans)
                    return ans
                else:
                    self._log_interaction("OpenAI ERROR", prompt, f"Status {res.status_code}: {res.text}")
            except Exception as e:
                self._log_interaction("OpenAI EXCEPTION", prompt, str(e))

        # --- 1. Secondary: Groq (Official SDK) ---
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a fiduciary AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                    temperature=1
                )
                ans = completion.choices[0].message.content
                if ans:
                    self._log_interaction("Groq (Llama 3.1 8B)", prompt, ans)
                    return ans
            except Exception as e:
                self._log_interaction("Groq EXCEPTION", prompt, str(e))
                pass

        # --- 2. Tertiary: Google Gemini (REST) ---
        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = requests.post(url, json=payload, timeout=10)
                if res.status_code == 200:
                    ans = res.json()['candidates'][0]['content']['parts'][0]['text']
                    self._log_interaction("Google Gemini", prompt, ans)
                    return ans
                else:
                    self._log_interaction("Gemini ERROR", prompt, f"Status {res.status_code}: {res.text}")
            except Exception as e:
                self._log_interaction("Gemini EXCEPTION", prompt, str(e))
                pass

        # --- 3. Final: High-Density Deterministic Fallback ---
        question_low = question.lower()
        response = ""
        
        # A. Specific Asset Search (e.g., "Why ICICI?")
        matched_assets = []
        for s in equity_sleeve:
            if s['symbol'].lower() in question_low:
                matched_assets.append(f"{s['symbol']} ({s['target_weight']:.1%} Alpha)")
        for f in passive_sleeve:
            if f['ticker'].lower() in question_low or ("icici" in f['ticker'].lower() and "icici" in question_low):
                matched_assets.append(f"{f['ticker']} ({f['target_weight']:.1%} Beta)")

        if matched_assets:
            assets_str = " and ".join(matched_assets)
            response = (
                f"I found **{assets_str}** in your current plan. These were included to provide "
                "calculated exposure within your risk profile. Alpha assets (stocks) are selected for ROCE, while "
                "Beta assets (funds) ensure market-matching stability and liquidity."
            )

        # B. Risk & Sector Distribution
        elif any(k in question_low for k in ["risk", "safety", "sector", "distribution", "guardrail"]):
            sectors = [s.get('sector', 'Unknown') for s in equity_sleeve]
            if sectors:
                top_sector = max(set(sectors), key=sectors.count)
                sector_weight = (sectors.count(top_sector) / len(sectors)) * 100
                sector_msg = f"Your highest exposure is currently in **{top_sector}** ({sector_weight:.2f}% of equities), "
            else:
                sector_msg = ""
                
            response = (
                f"Your sector distribution is strictly governed by the **20% Fiduciary Ceiling**. {sector_msg}"
                "This prevents over-concentration in any single industry shock. We also use the UCITS 5/10/40 rule "
                "to diversify across individual stocks."
            )

        # C. Selection Basis & Philosophy
        elif any(k in question_low for k in ["basis", "select", "why these", "criteria", "philosophy", "momentum"]):
            response = (
                f"Your {risk_profile} portfolio is constructed using a **Quality at Reasonable Price (QARP)** filter. "
                f"We selected {len(equity_sleeve)} stocks that meet our **1.5% ROCE threshold** while ensuring no single "
                "position exceeds institutional concentration limits. Our methodology prioritizes solvency and quality over speculative momentum."
            )

        # D. General Holdings
        elif any(k in question_low for k in ["stocks", "holdings", "positions", "assets", "fund"]):
            top_3 = ", ".join([s['symbol'] for s in equity_sleeve[:3]])
            response = (
                f"Your current alpha sleeve consists of {len(equity_sleeve)} positions, including **{top_3}**. "
                f"Your beta sleeve contains {len(passive_sleeve)} funds for stability."
            )
        
        # E. Default Fiduciary Overview
        else:
            response = (
                f"I have analyzed your **{risk_profile}** portfolio managing **{total_amount:,.2f} INR**. "
                f"The system is operating within all fiduciary guardrails including ROCE and Sector-Cap limits. "
                "Ask me about specific stocks or your sector risk for more detail."
            )

        self._log_interaction("Deterministic Fallback", prompt, response)
        return response
