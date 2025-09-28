from __future__ import annotations

from dataclasses import dataclass
import polars as pl

from .metrics import compute_kpis


@dataclass(frozen=True)
class HealthScore:
    score: float  # 0-100
    components: dict[str, float]


DEFAULT_WEIGHTS = {
    "savings_rate": 0.6,
    "expense_to_income": 0.25,
    "net_positive": 0.15,
}


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def compute_health_score(df: pl.DataFrame, weights: dict[str, float] | None = None) -> HealthScore:
    w = weights or DEFAULT_WEIGHTS
    kpis = compute_kpis(df)

    # Normalize components to 0..100
    savings_rate_pct = clamp(kpis.savings_rate * 100.0, 0.0, 100.0)
    expense_to_income = (kpis.total_expense / kpis.total_income) if kpis.total_income > 0 else 1.0
    expense_to_income_pct = clamp((1.0 - expense_to_income) * 100.0, 0.0, 100.0)
    net_positive_pct = clamp(100.0 if kpis.net_cashflow >= 0 else 0.0)

    score = (
        w.get("savings_rate", 0) * savings_rate_pct
        + w.get("expense_to_income", 0) * expense_to_income_pct
        + w.get("net_positive", 0) * net_positive_pct
    )

    # Normalize by sum of weights
    total_w = sum(w.values()) or 1.0
    score /= total_w
    score = clamp(score)

    components = {
        "savings_rate_pct": round(savings_rate_pct, 2),
        "expense_to_income_pct": round(expense_to_income_pct, 2),
        "net_positive_pct": round(net_positive_pct, 2),
    }
    return HealthScore(score=round(score, 1), components=components)
