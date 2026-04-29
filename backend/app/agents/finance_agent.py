FINANCE_SYSTEM_PROMPT = """You are an expert Finance Agent for an enterprise organization.

Your responsibilities include:
- Analyzing budgets, forecasts, and financial summaries
- Reviewing invoices, expenses, and payment records
- Identifying cost anomalies and spending trends
- Summarizing profit/loss statements and cash flow reports
- Answering questions about financial policies and procedures

Always cite the source document and relevant figures when referencing financial data.
Present numbers clearly with appropriate currency formatting where possible.
"""

_CATEGORY_KEYWORD_MAP: dict[str, list[str]] = {
    "budget": ["budget", "forecast", "plan", "allocation", "spend limit"],
    "invoice": ["invoice", "payment", "billing", "vendor", "purchase order", "po"],
    "expense": ["expense", "reimbursement", "cost", "receipt", "claim"],
    "revenue": ["revenue", "income", "profit", "earnings", "turnover", "sales"],
    "tax": ["tax", "vat", "gst", "deduction", "withholding", "fiscal"],
    "payroll": ["payroll", "salary", "wage", "compensation", "bonus", "commission"],
    "cashflow": ["cashflow", "cash flow", "liquidity", "working capital", "burn rate"],
}

_ANOMALY_THRESHOLDS = {
    "high_variance": 0.20,   # 20% deviation from expected
    "critical_variance": 0.50,  # 50% deviation — critical flag
}


class FinanceAgent:
    """
    Specialized agent for financial queries.
    Handles budgets, invoices, expenses, revenue, and financial reporting.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "analyst") -> str:
        """Build a structured prompt for the finance agent."""
        return (
            f"{FINANCE_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Question: {query}\n\n"
            f"Financial Documents / Data:\n{context or 'No documents provided.'}\n\n"
            "Provide a precise, data-driven answer with figures and source citations:"
        )

    def extract_categories(self, query: str) -> list[str]:
        """
        Extract finance-relevant categories from a query for targeted retrieval.
        Returns a list of matched category names.
        """
        lowered = query.lower()
        return [
            category
            for category, keywords in _CATEGORY_KEYWORD_MAP.items()
            if any(kw in lowered for kw in keywords)
        ] or ["general_finance"]

    def detect_anomaly(self, actual: float, expected: float) -> dict:
        """
        Detect if a financial figure deviates significantly from the expected value.
        Returns a dict with 'has_anomaly', 'severity', and 'variance_pct'.
        """
        if expected == 0:
            return {"has_anomaly": False, "severity": "none", "variance_pct": 0.0}

        variance_pct = abs(actual - expected) / abs(expected)

        if variance_pct >= _ANOMALY_THRESHOLDS["critical_variance"]:
            severity = "critical"
        elif variance_pct >= _ANOMALY_THRESHOLDS["high_variance"]:
            severity = "high"
        else:
            severity = "none"

        return {
            "has_anomaly": severity != "none",
            "severity": severity,
            "variance_pct": round(variance_pct * 100, 2),
        }

    def format_summary(self, title: str, line_items: list[dict]) -> str:
        """
        Format a financial summary report.
        Each line_item dict should have 'label' and 'amount' keys.
        """
        if not line_items:
            return f"## {title}\n\nNo financial data available."

        lines = [f"## {title}\n"]
        total = 0.0
        for item in line_items:
            label = item.get("label", "Unknown")
            amount = item.get("amount", 0.0)
            total += amount
            lines.append(f"- {label}: ${amount:,.2f}")
        lines.append(f"\n**Total: ${total:,.2f}**")
        return "\n".join(lines)

    def calculate_variance(self, actual: float, budget: float) -> dict:
        """
        Calculate the variance between actual spend and budget.
        Returns a dict with 'variance', 'variance_pct', and 'status'.
        """
        variance = actual - budget
        variance_pct = (variance / budget * 100) if budget != 0 else 0.0
        status = "over_budget" if variance > 0 else "under_budget" if variance < 0 else "on_budget"
        return {
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "status": status,
        }
