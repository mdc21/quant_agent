# Implementation Plan: Full-Stack Migration (React + FastAPI)

This plan details the migration of the **YourBestPath** platform from a Streamlit-based application to a robust Full-Stack architecture, adopting the sophisticated **Wealth Navigator Pro** UI.

## Architecture
- **Frontend**: React + Vite + Tailwind CSS (based on the provided zip).
- **Backend**: FastAPI (Python) to expose existing quant and fiduciary logic.
- **Database**: ArcticDB (persisting goals, portfolios, and user data).
- **Communication**: REST API with JWT-based authentication.

---

## Phase 1: Backend Development (FastAPI)
- **[NEW] `server/main.py`**: Entry point for the FastAPI server.
- **[NEW] `server/api/auth.py`**: Endpoints for `/api/register` and `/api/login` (using `core/auth/user_store.py`).
- **[NEW] `server/api/goals.py`**: Endpoints for `/api/goals` (Get/Update).
- **[NEW] `server/api/portfolio.py`**: Endpoints for `/api/portfolio` (Fetch holdings, run rebalancer).
- **[NEW] `server/api/market.py`**: Endpoints for fetching live prices/indices.

## Phase 2: Frontend Migration (React)
- **[MOVE] `temp_wealth_navigator/` -> `frontend/`**
- **[MODIFY] `frontend/package.json`**: Ensure all dependencies are aligned.
- **[MODIFY] `frontend/src/lib/api.ts`**: Create a central API client to communicate with the FastAPI server.
- **[MODIFY] `frontend/src/routes/auth.tsx`**: Connect the sign-in/sign-up forms to the backend.

## Phase 3: Logic Porting & Integration
- Migrate logic from `app/pages/goals_wizard.py` (goal definition logic) into the backend.
- Migrate logic from `app/dashboard.py` (portfolio summary logic) into the backend.
- Connect the React "Fiduciary Hub" to real data from ArcticDB.

---

## Verification Plan

### Automated Testing
- Unit tests for new API endpoints in `tests/api/`.
- `pytest tests/api`

### Manual Verification
1.  **Start Backend**: `uvicorn server.main:app --reload --port 8000`
2.  **Start Frontend**: `cd frontend && npm run dev`
3.  **End-to-End Test**:
    - Register a new user.
    - Log in and verify session.
    - Complete the Goals Wizard.
    - View the generated portfolio in the Dashboard.
    - Run a "Quick Advice" simulation.
