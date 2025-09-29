from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import polars as pl

from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
try:
    from langchain_ollama import ChatOllama  # type: ignore
except Exception:  # pragma: no cover
    ChatOllama = None  # type: ignore

from ..settings.config import get_config
from ..analytics.metrics import compute_kpis, monthly_cashflow, category_breakdown
from ..analytics.scoring import compute_health_score
from .langchain_tools import (
    get_kpis,
    get_monthly_cashflow_csv,
    get_top_categories_csv,
    get_top_merchants_csv,
    compute_health_score as tool_compute_health_score,
    save_advice,
)
from .sanitize import sanitize_output

SYSTEM_PROMPT = (
    "You are a local financial health advisor. You can call tools to retrieve metrics. "
    "Output ONLY the final answer in clean Markdown, no chain-of-thought. Format sections: At a glance, Key insights, Opportunities, Actions this month, Watchouts."
)

INSTRUCTIONS = (
    "Given a session_id, call tools to fetch KPIs, monthly cashflow, categories and merchants. "
    "Then write a short prioritized advice section tailored to the data. "
    "When finished, call save_advice to persist the recommendation."
)


@dataclass
class LangChainAdviceResult:
    score: float
    components: Dict[str, float]
    advice_markdown: str


class LangChainAdviceAgent:
    def __init__(self):
        self.cfg = get_config()
        if ChatOllama is None:
            raise ImportError("langchain_ollama is not installed. Install or set ADVICE_BACKEND=ollama_direct.")
        self.llm = ChatOllama(model=self.cfg.ollama_model, base_url=self.cfg.ollama_host)
        self.tools = [
            get_kpis,
            get_monthly_cashflow_csv,
            get_top_categories_csv,
            get_top_merchants_csv,
            tool_compute_health_score,
            save_advice,
        ]
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "Session ID: {session_id}\n\n" + INSTRUCTIONS),
        ])
        # Use ReAct agent for broad model compatibility (no function-calling required)
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=False)

    def generate(self, df: pl.DataFrame, session_id: str | None = None) -> LangChainAdviceResult:
        # We still compute baseline score locally to show immediately while agent runs
        hs = compute_health_score(df)
        _sid = session_id or "unknown"
        result = self.executor.invoke({"session_id": _sid})
        content = result.get("output", "")
        content = sanitize_output(content)
        return LangChainAdviceResult(score=hs.score, components=hs.components, advice_markdown=content)
