from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import polars as pl

from ..settings.config import get_config
from ..analytics.metrics import compute_kpis, monthly_cashflow, category_breakdown
from ..analytics.scoring import compute_health_score
from ..analytics.insights import top_expense_transactions, recurring_candidates, subscription_merchants
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


@dataclass
class AdviceResult:
    score: float
    components: dict[str, float]
    advice_markdown: str


class AdviceEngine:
    def __init__(self):
        self.cfg = get_config()

    def _format_df(self, df: pl.DataFrame, limit: int = 12) -> str:
        if df.is_empty():
            return "<empty>"
        # Avoid optional tabulate dependency; use CSV for compactness
        return df.head(limit).to_pandas().to_csv(index=False)

    def _direct_ollama(self, user_prompt: str, hs) -> "AdviceResult":
        try:
            from ollama import Client  # lazy import
        except Exception:
            return AdviceResult(
                score=hs.score,
                components=hs.components,
                advice_markdown=(
                    "Ollama client not available. Install and run Ollama to get AI advice.\n\n"
                    "Quick tips:\n"
                    "- Increase savings rate by 5–10% via auto-transfers.\n"
                    "- Reduce top 2 discretionary categories by 15%.\n"
                    "- Review recurring charges and cancel unused subscriptions.\n"
                ),
            )

        client = Client(host=self.cfg.ollama_host)
        resp = client.chat(
            model=self.cfg.ollama_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
        )
        advice_text = resp.get("message", {}).get("content", "").strip()
        return AdviceResult(score=hs.score, components=hs.components, advice_markdown=advice_text)

    def generate(self, df: pl.DataFrame, session_id: str | None = None) -> AdviceResult:
        hs = compute_health_score(df)
        cats = category_breakdown(df)
        monthly = monthly_cashflow(df)
        kpis = compute_kpis(df)

        # Build additional context for specificity
        top_tx = top_expense_transactions(df, limit=8).to_pandas().to_csv(index=False)
        recurr = recurring_candidates(df, min_count=2, limit=10).to_pandas().to_csv(index=False)
        subs = subscription_merchants(df, limit=10).to_pandas().to_csv(index=False)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            metrics=(
                f"total_income: {kpis.total_income:.2f}, "
                f"total_expense: {kpis.total_expense:.2f}, "
                f"net_cashflow: {kpis.net_cashflow:.2f}, "
                f"savings_rate: {kpis.savings_rate:.2f}"
            ),
            categories=self._format_df(cats, limit=10),
            monthly=self._format_df(monthly, limit=12),
            score=hs.score,
        ) + (
            "\n\nTop individual expenses (CSV):\n" + top_tx +
            "\nRecurring charge candidates (CSV):\n" + recurr +
            "\nSubscriptions by merchant (CSV):\n" + subs
        )

        if self.cfg.advice_backend == "langchain":
            try:
                from .langchain_agent import LangChainAdviceAgent  # lazy import to avoid hard dependency
                agent = LangChainAdviceAgent()
                res = agent.generate(df, session_id=session_id)
                return AdviceResult(score=res.score, components=res.components, advice_markdown=res.advice_markdown)
            except Exception:
                return self._direct_ollama(user_prompt, hs)
        else:
            return self._direct_ollama(user_prompt, hs)
