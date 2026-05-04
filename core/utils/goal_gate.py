"""
GoalGateEngine — Fiduciary Portfolio Mode Selector
====================================================
Reads the investor's goal funding status and returns the correct
portfolio construction mode. This prevents the engine from recommending
aggressive equities when the investor has not yet secured their
Survival or Safety foundation.

Modes
-----
SURVIVAL_MODE   Survival < 100% funded → only liquid/defensive assets
SAFETY_MODE     Survival funded, Safety < 50%  → debt + gold + beta equity only
GROWTH_MODE     Safety >= 50% funded → full alpha + beta (current default)
"""

from dataclasses import dataclass
from typing import List, Dict, Any


SURVIVAL_MODE = "SURVIVAL_MODE"
SAFETY_MODE   = "SAFETY_MODE"
GROWTH_MODE   = "GROWTH_MODE"


@dataclass
class GoalGateResult:
    mode: str
    banner_color: str
    banner_icon: str
    headline: str
    rationale: str
    allowed_equity: bool
    allowed_beta: bool
    allowed_liquid: bool
    equity_cap_pct: float    # max % of capital that can go to direct equity
    beta_cap_pct: float      # max % to passive equity ETFs
    defensive_cap_pct: float # min % to liquid/debt/gold


def evaluate_goal_gate(goal_results: List[Dict[str, Any]]) -> GoalGateResult:
    """
    Given a list of GIA feasibility results (each with label, target_value,
    median_outcome, current_assets), return the GoalGateResult that
    constrains portfolio construction.

    Parameters
    ----------
    goal_results : list of dicts from gia.run_feasibility_check() enriched
                   with sleeve.current_assets and sleeve.target_value.
    """
    survival = next((r for r in goal_results if r["label"] == "Survival"), None)
    safety   = next((r for r in goal_results if r["label"] == "Safety"),   None)

    # --- Survival Gate ---
    surv_funded = _funding_pct(survival)
    safe_funded  = _funding_pct(safety)

    if surv_funded < 1.0:
        # Survival not fully funded — lock everything except liquid/defensive
        return GoalGateResult(
            mode=SURVIVAL_MODE,
            banner_color="#f43f5e",
            banner_icon="🚨",
            headline="SURVIVAL MODE — Fiduciary Lock Active",
            rationale=(
                f"Your Survival (Emergency Fund) is only {surv_funded:.0%} funded. "
                "Until this is secured, the engine will only allocate capital to "
                "**liquid and defensive instruments** (overnight funds, short-duration "
                "debt, gold ETFs). Direct equity and equity mutual funds are locked."
            ),
            allowed_equity=False,
            allowed_beta=False,
            allowed_liquid=True,
            equity_cap_pct=0.0,
            beta_cap_pct=0.0,
            defensive_cap_pct=1.0,
        )

    if safe_funded < 0.5:
        # Survival funded but Safety < 50% — allow debt-skewed beta only
        return GoalGateResult(
            mode=SAFETY_MODE,
            banner_color="#f59e0b",
            banner_icon="⚠️",
            headline="SAFETY MODE — Equity Restricted",
            rationale=(
                f"Survival is secured ✅, but your Safety (Retirement) goal is only "
                f"{safe_funded:.0%} funded. The engine will prioritise **debt, gold, "
                "and balanced passive funds** (GILTBEES, GOLDBEES, balanced advantage "
                "funds). Direct equity is capped at 20% of capital."
            ),
            allowed_equity=True,
            allowed_beta=True,
            allowed_liquid=True,
            equity_cap_pct=0.20,    # max 20% to direct stocks
            beta_cap_pct=0.40,      # 40% to beta equity ETFs
            defensive_cap_pct=0.40, # 40% to liquid/debt/gold
        )

    # Full Growth Mode
    return GoalGateResult(
        mode=GROWTH_MODE,
        banner_color="#10b981",
        banner_icon="✅",
        headline="GROWTH MODE — Full Portfolio Unlocked",
        rationale=(
            f"Survival ✅ and Safety ({safe_funded:.0%} funded) thresholds are met. "
            "The engine will generate a full fiduciary portfolio: alpha (direct equity) "
            "+ beta (passive equity funds) + defensive (liquid/debt/gold)."
        ),
        allowed_equity=True,
        allowed_beta=True,
        allowed_liquid=True,
        equity_cap_pct=0.60,
        beta_cap_pct=0.25,
        defensive_cap_pct=0.15,
    )


def _funding_pct(result: Dict[str, Any]) -> float:
    """Return what fraction of the target the median outcome covers."""
    if result is None:
        return 1.0  # no goal defined → don't block
    target  = result.get("target_value", 1)
    outcome = result.get("median_outcome", 0)
    if target <= 0:
        return 1.0
    return min(1.0, outcome / target)
