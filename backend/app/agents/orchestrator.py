from typing import Literal

AgentType = Literal["hr", "finance", "compliance", "analytics", "general"]

_HR_KEYWORDS = {
    "onboard", "payroll", "leave", "recruit", "hire", "benefit",
    "vacation", "salary", "employee", "hr", "pto", "bonus", "handbook",
    "performance", "review", "termination", "resignation",
}
_FINANCE_KEYWORDS = {
    "budget", "invoice", "expense", "revenue", "financial", "cost",
    "profit", "loss", "forecast", "spend", "payment", "tax", "ledger",
    "accounting", "cashflow",
}
_COMPLIANCE_KEYWORDS = {
    "compliance", "policy", "audit", "regulation", "risk", "violation",
    "gdpr", "hipaa", "sox", "clause", "legal", "contract", "breach",
    "liability", "regulatory",
}
_ANALYTICS_KEYWORDS = {
    "trend", "insight", "analyze", "report", "metric", "kpi",
    "growth", "performance", "statistic", "dashboard", "data", "chart",
    "compare", "quarterly", "annually",
}

_KEYWORD_MAP: dict[AgentType, set[str]] = {
    "hr": _HR_KEYWORDS,
    "finance": _FINANCE_KEYWORDS,
    "compliance": _COMPLIANCE_KEYWORDS,
    "analytics": _ANALYTICS_KEYWORDS,
}


def classify_query(query: str) -> AgentType:
    """
    Classify a user query to determine which specialized agent should handle it.
    Returns the agent type with the highest keyword match score.
    Falls back to 'general' if no keywords match.
    """
    lowered = query.lower()
    scores: dict[AgentType, int] = {
        agent: sum(1 for kw in keywords if kw in lowered)
        for agent, keywords in _KEYWORD_MAP.items()
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "general"


class OrchestratorAgent:
    """
    Routes user queries to the appropriate specialized agent.
    Acts as the main brain of the multi-agent system.
    """

    AGENT_DESCRIPTIONS: dict[AgentType, str] = {
        "hr": "HR Agent — handles onboarding, payroll, leave, recruitment, and HR policies.",
        "finance": "Finance Agent — handles budgets, invoices, expenses, and financial summaries.",
        "compliance": "Compliance Agent — checks policy violations, contract clauses, and audit risks.",
        "analytics": "Analytics Agent — analyzes trends, metrics, and generates data insights.",
        "general": "General Agent — handles general knowledge and retrieval queries.",
    }

    def route(self, query: str) -> dict:
        """
        Determine which agent should handle the given query.
        Returns a dict with 'active_agent' and 'agent_description'.
        """
        agent = classify_query(query)
        return {
            "active_agent": agent,
            "agent_description": self.AGENT_DESCRIPTIONS[agent],
        }
