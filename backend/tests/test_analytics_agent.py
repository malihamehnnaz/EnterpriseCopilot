import pytest
from backend.app.agents.analytics_agent import AnalyticsAgent


class TestAnalyticsAgentBuildPrompt:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("What are the Q3 trends?", "Trend data here.")
        assert "What are the Q3 trends?" in prompt

    def test_prompt_contains_context(self):
        context = "Sales grew by 15% in Q3."
        prompt = self.agent.build_prompt("Summarize performance", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("KPI summary", "", user_role="executive")
        assert "executive" in prompt

    def test_prompt_defaults_to_analyst_role(self):
        prompt = self.agent.build_prompt("Show KPIs", "")
        assert "analyst" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("Trends?", "")
        assert "No data provided." in prompt


class TestAnalyticsAgentDetectTrend:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_detects_growth(self):
        result = self.agent.detect_trend([100, 110, 125, 140])
        assert result["direction"] == "growth"
        assert result["change_pct"] == 40.0
        assert result["is_significant"] is True

    def test_detects_decline(self):
        result = self.agent.detect_trend([100, 90, 80, 70])
        assert result["direction"] == "decline"
        assert result["change_pct"] == -30.0

    def test_detects_flat(self):
        result = self.agent.detect_trend([100, 102, 99, 101])
        assert result["direction"] == "flat"

    def test_insufficient_data(self):
        result = self.agent.detect_trend([100])
        assert result["direction"] == "insufficient_data"

    def test_empty_data(self):
        result = self.agent.detect_trend([])
        assert result["direction"] == "insufficient_data"

    def test_handles_zero_first_value(self):
        result = self.agent.detect_trend([0, 100, 200])
        assert result["direction"] == "unknown"

    def test_not_significant_when_small_change(self):
        result = self.agent.detect_trend([100, 105])
        assert result["is_significant"] is False


class TestAnalyticsAgentComputeStats:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_computes_mean(self):
        stats = self.agent.compute_stats([10, 20, 30])
        assert stats["mean"] == 20.0

    def test_computes_min_max(self):
        stats = self.agent.compute_stats([5, 15, 25])
        assert stats["min"] == 5.0
        assert stats["max"] == 25.0

    def test_computes_count(self):
        stats = self.agent.compute_stats([1, 2, 3, 4, 5])
        assert stats["count"] == 5

    def test_std_dev_zero_for_single_value(self):
        stats = self.agent.compute_stats([42.0])
        assert stats["std_dev"] == 0.0

    def test_handles_empty_list(self):
        stats = self.agent.compute_stats([])
        assert stats["count"] == 0
        assert stats["mean"] == 0.0


class TestAnalyticsAgentComparePeriods:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_direction_up(self):
        result = self.agent.compare_periods(current=120, previous=100, label="Revenue")
        assert result["direction"] == "up"
        assert result["change_pct"] == 20.0

    def test_direction_down(self):
        result = self.agent.compare_periods(current=80, previous=100, label="Revenue")
        assert result["direction"] == "down"
        assert result["change_pct"] == -20.0

    def test_direction_flat(self):
        result = self.agent.compare_periods(current=100, previous=100)
        assert result["direction"] == "flat"

    def test_handles_zero_previous(self):
        result = self.agent.compare_periods(current=100, previous=0)
        assert result["direction"] == "unknown"
        assert result["change_pct"] == 0.0

    def test_label_in_result(self):
        result = self.agent.compare_periods(current=50, previous=40, label="Conversions")
        assert result["label"] == "Conversions"


class TestAnalyticsAgentClassifySentiment:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_positive_sentiment(self):
        assert self.agent.classify_sentiment("Sales improved and revenue grew significantly.") == "positive"

    def test_negative_sentiment(self):
        assert self.agent.classify_sentiment("Revenue declined and profits fell this quarter.") == "negative"

    def test_neutral_sentiment(self):
        assert self.agent.classify_sentiment("The report covers the quarter's activities.") == "neutral"


class TestAnalyticsAgentFormatKpiReport:
    def setup_method(self):
        self.agent = AnalyticsAgent()

    def test_report_has_header(self):
        kpis = [{"name": "Revenue", "value": 1_000_000, "unit": "$"}]
        report = self.agent.format_kpi_report(kpis)
        assert "KPI Report" in report

    def test_report_contains_kpi_name(self):
        kpis = [{"name": "Churn Rate", "value": 5, "unit": "%"}]
        report = self.agent.format_kpi_report(kpis)
        assert "Churn Rate" in report

    def test_report_shows_target_status(self):
        kpis = [{"name": "NPS", "value": 45, "unit": "", "target": 40}]
        report = self.agent.format_kpi_report(kpis)
        assert "✓" in report

    def test_report_shows_miss_target(self):
        kpis = [{"name": "NPS", "value": 30, "unit": "", "target": 40}]
        report = self.agent.format_kpi_report(kpis)
        assert "✗" in report

    def test_handles_empty_kpis(self):
        assert self.agent.format_kpi_report([]) == "No KPI data available."
