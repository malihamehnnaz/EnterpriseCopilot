from statistics import mean, stdev
from typing import Any

ANALYTICS_SYSTEM_PROMPT = """You are an expert Analytics Agent for an enterprise organization.

Your responsibilities include:
- Identifying trends, patterns, and anomalies in business data
- Generating data-driven insights from reports and metrics
- Comparing performance across time periods (quarterly, annually)
- Summarizing KPIs and dashboards
- Answering questions about business intelligence and analytics

Always provide specific figures, percentage changes, and directional trends (up/down/flat).
Clearly state the time period or data source for every insight.
"""

_TREND_KEYWORDS: dict[str, list[str]] = {
    "growth": ["increase", "grew", "growth", "up", "rise", "gain", "improved"],
    "decline": ["decrease", "declined", "drop", "down", "fell", "loss", "reduced"],
    "flat": ["stable", "flat", "unchanged", "consistent", "steady", "maintained"],
}


class AnalyticsAgent:
    """
    Specialized agent for analytics and business intelligence queries.
    Handles trends, KPIs, metrics, insights, and comparative reporting.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "analyst") -> str:
        """Build a structured prompt for the analytics agent."""
        return (
            f"{ANALYTICS_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Query: {query}\n\n"
            f"Data / Reports:\n{context or 'No data provided.'}\n\n"
            "Provide a clear, insight-driven analysis with specific figures and trends:"
        )

    def detect_trend(self, values: list[float]) -> dict:
        """
        Detect the trend direction from a time-series list of values.
        Returns a dict with 'direction', 'change_pct', and 'is_significant'.
        """
        if len(values) < 2:
            return {"direction": "insufficient_data", "change_pct": 0.0, "is_significant": False}

        first = values[0]
        last = values[-1]

        if first == 0:
            return {"direction": "unknown", "change_pct": 0.0, "is_significant": False}

        change_pct = ((last - first) / abs(first)) * 100

        if change_pct > 5:
            direction = "growth"
        elif change_pct < -5:
            direction = "decline"
        else:
            direction = "flat"

        return {
            "direction": direction,
            "change_pct": round(change_pct, 2),
            "is_significant": abs(change_pct) >= 10,
        }

    def compute_stats(self, values: list[float]) -> dict:
        """
        Compute basic descriptive statistics for a dataset.
        Returns mean, min, max, and standard deviation.
        """
        if not values:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0, "count": 0}

        return {
            "mean": round(mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "std_dev": round(stdev(values), 2) if len(values) > 1 else 0.0,
            "count": len(values),
        }

    def compare_periods(self, current: float, previous: float, label: str = "metric") -> dict:
        """
        Compare a metric between two periods and return a structured comparison.
        """
        if previous == 0:
            return {
                "label": label,
                "current": current,
                "previous": previous,
                "change": current,
                "change_pct": 0.0,
                "direction": "unknown",
            }

        change = current - previous
        change_pct = (change / abs(previous)) * 100
        direction = "up" if change > 0 else "down" if change < 0 else "flat"

        return {
            "label": label,
            "current": round(current, 2),
            "previous": round(previous, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "direction": direction,
        }

    def classify_sentiment(self, text: str) -> str:
        """
        Classify the performance sentiment of a text snippet.
        Returns 'positive', 'negative', or 'neutral'.
        """
        lowered = text.lower()
        growth_hits = sum(1 for kw in _TREND_KEYWORDS["growth"] if kw in lowered)
        decline_hits = sum(1 for kw in _TREND_KEYWORDS["decline"] if kw in lowered)

        if growth_hits > decline_hits:
            return "positive"
        elif decline_hits > growth_hits:
            return "negative"
        return "neutral"

    def format_kpi_report(self, kpis: list[dict]) -> str:
        """
        Format a list of KPI dicts into a readable report.
        Each KPI dict should have 'name', 'value', and optionally 'target' and 'unit'.
        """
        if not kpis:
            return "No KPI data available."

        lines = ["## KPI Report\n"]
        for kpi in kpis:
            name = kpi.get("name", "Unknown KPI")
            value = kpi.get("value", 0)
            unit = kpi.get("unit", "")
            target = kpi.get("target")

            line = f"- **{name}**: {value}{unit}"
            if target is not None:
                status = "✓" if value >= target else "✗"
                line += f" / Target: {target}{unit} [{status}]"
            lines.append(line)

        return "\n".join(lines)
