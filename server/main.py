import os
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from typing import List, Dict, Any, Optional
import datetime
import math

from core.auth.user_store import UserStore
from core.data.store import DataStore
from core.data.historical_provider import HistoricalProvider
from server.models import (
    LoginRequest, RegisterRequest, GoalsUpdateRequest, GoalConfig, 
    QuickAdviceRequest, PortfolioUploadRequest, PortfolioReviewResponse, 
    RebalanceAction, Holding, ChatRequest
)
from server.constants import GOAL_CATALOG, QUICK_ADVICE_ALLOCATIONS
from app.agents.allocator import PathAllocator
from app.agents.insa import InsightNarrativeEngine
from core.utils.symbol_mapper import SymbolMapper
import yfinance as yf

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_nan(obj):
    """Recursively replace NaN values with 0 for JSON compatibility."""
    if isinstance(obj, float) and math.isnan(obj):
        return 0
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    return obj

app = FastAPI(title="YourBestPath API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTH ENDPOINTS ---
@app.post("/api/auth/login")
async def login(req: LoginRequest):
    store = UserStore()
    result = store.authenticate(req.email, req.password)
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    store = UserStore()
    result = store.register(req.name, req.email, req.password)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# --- GOALS ENDPOINTS ---
@app.get("/api/goals/catalog")
async def get_catalog():
    return GOAL_CATALOG

@app.get("/api/goals/{user_key}")
async def get_user_goals(user_key: str):
    ds = DataStore()
    goals = ds.get_goals(user_key)
    return goals

@app.post("/api/goals/save")
async def save_goals(req: GoalsUpdateRequest):
    ds = DataStore()
    try:
        goals_list = [g.model_dump() for g in req.goals]
        ds.save_goals(
            req.user_key, 
            goals_list,
            risk_tolerance=req.risk_profile,
            inflation_rate=req.inflation_rate
        )
        store = UserStore()
        store.update_profile(req.user_key, {"onboarding_complete": True, "risk_profile": req.risk_profile})
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to save goals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- PORTFOLIO & ADVICE ENDPOINTS ---
@app.get("/api/portfolio/{user_key}")
async def get_portfolio(user_key: str):
    ds = DataStore()
    res = ds.get_portfolio(user_key)
    logger.info(f"Raw portfolio requested for {user_key}. Returning {len(res.get('holdings', []))} items.")
    return res

@app.post("/api/portfolio/upload")
async def upload_portfolio(req: PortfolioUploadRequest):
    ds = DataStore()
    # Logic to save imported_portfolio (I'll use ds.save_portfolio if it exists, or just store it as a special goal/asset)
    # Actually, let's use DataStore.save_user_portfolio
    try:
        holdings_list = [h.model_dump() for h in req.holdings]
        # Calculate live value during upload
        total_val = 0
        for h in holdings_list:
            try:
                yt = SymbolMapper.to_yahoo(h['symbol'])
                price = yf.Ticker(f"{yt}.NS").history(period="1d")["Close"].iloc[-1]
                h['current_price'] = float(price)
                h['market_value'] = float(price * h['quantity'])
                total_val += h['market_value']
            except:
                h['current_price'] = h['avg_price']
                h['market_value'] = h['avg_price'] * h['quantity']
                total_val += h['market_value']
        
        ds.save_portfolio(req.user_key, holdings_list)
        return {"success": True, "total_value": total_val}
    except Exception as e:
        logger.error(f"Portfolio upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/review/{user_key}")
async def review_portfolio(user_key: str):
    ds = DataStore()
    goals = ds.get_goals(user_key)
    if not goals:
        raise HTTPException(status_code=404, detail="No goals defined for this user.")
    
    portfolio_data = ds.get_portfolio(user_key)
    holdings = portfolio_data.get("holdings", []) if portfolio_data else []
    logger.info(f"Review requested for {user_key}. Found {len(holdings)} existing holdings.")
    
    # Calculate total capital (either from holdings or a default if new)
    total_cap = sum(h.get('market_value', 0) for h in holdings)
    if total_cap == 0:
        # Default for plan only
        total_cap = 1000000 
    
    store = UserStore()
    profile = store.get_profile(user_key)
    risk = profile.get("risk_profile", "Moderate")
    
    # Calculate target_year from goals (Horizon matching)
    target_year = 2030
    if goals:
        try:
            # Find the furthest goal year
            years = [int(g.get('target_year', 2030)) for g in goals if g.get('target_year')]
            if years:
                target_year = max(years)
        except:
            pass

    # Run PathAllocator
    allocator = PathAllocator(
        risk_profile=risk,
        total_capital=total_cap,
        target_year=target_year
    )
    
    # Map current portfolio for allocator
    current_port_map = {h['symbol']: h.get('market_value', 0)/total_cap for h in holdings if total_cap > 0}
    
    equity_sleeve, research_universe = allocator.build_equity_sleeve(current_portfolio=current_port_map)
    passive_sleeve = allocator.build_passive_sleeve()
    
    # Calculate Rebalance Plan and Tax
    from app.agents.toa import TaxOptimizationAgent
    from core.data.agent_schema import TaxLot
    toa = TaxOptimizationAgent()
    target_map = {s['symbol']: s['target_capital'] for s in equity_sleeve}
    rebalance_plan = []
    total_est_tax = 0.0
    
    # 1. Existing assets
    for h in holdings:
        sym = h['symbol']
        curr_val = h.get('market_value', 0)
        target_val = target_map.get(sym, 0)
        diff = target_val - curr_val
        
        action = "HOLD"
        est_tax = 0.0
        qty = int(h.get('quantity', 0)) if not math.isnan(h.get('quantity', 0)) else 0
        
        if target_val == 0: 
            action = "EXIT"
            # Calculate tax on full sale
            lot = TaxLot(symbol=sym, buy_price=h['avg_price'], buy_date=None, quantity=qty, current_price=h.get('current_price', h['avg_price']))
            est_tax = toa.calculate_lot_tax(lot, qty)
        elif diff < (-0.1 * curr_val): 
            action = "TRIM"
            # Calculate tax on partial sale
            sell_qty = int((abs(diff) / curr_val) * qty)
            lot = TaxLot(symbol=sym, buy_price=h['avg_price'], buy_date=None, quantity=qty, current_price=h.get('current_price', h['avg_price']))
            est_tax = toa.calculate_lot_tax(lot, sell_qty)
        elif diff > (0.1 * curr_val): 
            action = "TOP-UP"
        
        total_est_tax += est_tax
        
        rebalance_plan.append({
            "symbol": sym,
            "action": action,
            "current_value": curr_val,
            "target_value": target_val,
            "diff": diff,
            "est_tax": est_tax,
            "is_harvest": h.get('current_price', 0) < h['avg_price'] if h['avg_price'] > 0 else False
        })
        
    # 2. New buys
    imp_syms = set(h['symbol'] for h in holdings)
    for s in equity_sleeve:
        if s['symbol'] not in imp_syms:
            rebalance_plan.append({
                "symbol": s['symbol'],
                "action": "BUY",
                "current_value": 0,
                "target_value": s['target_capital'],
                "diff": s['target_capital'],
                "est_tax": 0.0,
                "is_harvest": False
            })
            
    # --- COMPARISON LOGIC ---
    mapper = SymbolMapper()
    
    # 1. Current Sector Exposure
    current_sectors: Dict[str, float] = {}
    for h in holdings:
        sec = mapper.get_sector(h['symbol'])
        current_sectors[sec] = current_sectors.get(sec, 0) + h.get('market_value', 0)
    
    # 2. Proposed Sector Exposure
    proposed_sectors: Dict[str, float] = {}
    for s in equity_sleeve:
        sec = s.get('sector', 'Others')
        proposed_sectors[sec] = proposed_sectors.get(sec, 0) + s.get('target_capital', 0)
    
    # Normalize Comparison Data
    comparison = {
        "sectors": [],
        "asset_classes": [
            {"label": "Direct Equity", "current": sum(h.get('market_value', 0) for h in holdings), "proposed": allocator.target_equity_capital},
            {"label": "Passive/Funds", "current": 0, "proposed": allocator.target_defensive_capital * 0.4}, # Approximation
            {"label": "Defensive", "current": 0, "proposed": allocator.target_defensive_capital * 0.6}
        ]
    }
    
    all_sectors = set(current_sectors.keys()) | set(proposed_sectors.keys())
    for sec in sorted(all_sectors):
        comparison["sectors"].append({
            "name": sec,
            "current": current_sectors.get(sec, 0),
            "proposed": proposed_sectors.get(sec, 0)
        })

    # Narrative
    insa = InsightNarrativeEngine()
    narrative = insa.generate_summary({
        "equity_sleeve": equity_sleeve,
        "passive_sleeve": passive_sleeve,
        "risk_profile": risk
    })
    
    return clean_nan({
        "equity_sleeve": equity_sleeve,
        "research_universe": research_universe,
        "passive_sleeve": passive_sleeve,
        "rebalance_plan": rebalance_plan,
        "total_est_tax": total_est_tax,
        "comparison": comparison,
        "metrics": {
            "total_capital": total_cap,
            "equity_cap": allocator.target_equity_capital,
            "defensive_cap": allocator.target_defensive_capital,
            "risk_profile": risk
        },
        "narrative": narrative
    })

@app.post("/api/portfolio/quick-advice")
async def get_quick_advice(req: QuickAdviceRequest):
    # Map risk profiles from frontend ("Growth", "Balanced", "Conservative") to backend ("Aggressive", "Balanced", "Conservative")
    risk_map = {"Growth": "Aggressive", "Balanced": "Balanced", "Conservative": "Conservative"}
    risk = risk_map.get(req.risk_profile, "Balanced")
    
    total_amount = req.amount
    if req.investment_type == "SIP":
        total_amount = req.amount * 12 # Optimize based on annual capital
        
    # Map horizon to target_year for consistent recruitment logic
    curr_year = datetime.datetime.now().year
    horizon_map = {"short": 3, "medium": 5, "long": 10}
    years = horizon_map.get(req.horizon, 10)
    target_year = curr_year + years
        
    allocator = PathAllocator(
        risk_profile=risk,
        total_capital=total_amount,
        target_year=target_year
    )
    
    equity_sleeve, research_universe = allocator.build_equity_sleeve()
    passive_sleeve = allocator.build_passive_sleeve()
    
    # Simple Narrative
    insa = InsightNarrativeEngine()
    narrative = insa.generate_summary({
        "equity_sleeve": equity_sleeve,
        "passive_sleeve": passive_sleeve,
        "risk_profile": risk
    })
    
    return clean_nan({
        "equity_sleeve": equity_sleeve,
        "research_universe": research_universe,
        "passive_sleeve": passive_sleeve,
        "metrics": {
            "total_capital": total_amount,
            "equity_cap": allocator.target_equity_capital,
            "defensive_cap": allocator.target_defensive_capital,
            "risk_profile": risk,
            "type": req.investment_type
        },
        "narrative": narrative
    })

@app.post("/api/auth/chat")
async def fiduciary_chat(req: ChatRequest):
    insa = InsightNarrativeEngine()
    
    # If no context is provided, we try to build it from the user's current data
    context = req.context
    if not context:
        store = UserStore()
        ds = DataStore()
        profile = store.get_profile(req.user_key)
        portfolio_data = ds.get_portfolio(req.user_key)
        holdings = portfolio_data.get("holdings", [])
        
        context = {
            "risk_profile": profile.get("risk_profile", "Moderate"),
            "investor_portfolio": holdings,
            "amount": sum(h.get('market_value', 0) for h in holdings)
        }
    
    answer = insa.chat(req.question, context, req.history)
    return {"answer": answer}

# --- MARKET DATA ENDPOINTS ---
@app.get("/api/market/price/{symbol}")
async def get_price_series(symbol: str, days: int = 180):
    try:
        hp = HistoricalProvider()
        series = hp.get_price_series(symbol, lookback_days=days)
        if series.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Format for charts: list of {date: str, price: float}
        data = [{"date": dt.strftime("%Y-%m-%d"), "price": float(val)} for dt, val in series.items()]
        return data
    except Exception as e:
        logger.error(f"Market data fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "YourBestPath API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
