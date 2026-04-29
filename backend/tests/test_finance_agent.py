import pytest
from backend.app.agents.finance_agent import FinanceAgent


class TestFinanceAgentBuildPrompt:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("What is the Q3 budget?", "Budget data here.")
        assert "What is the Q3 budget?" in prompt

    def test_prompt_contains_context(self):
        context = "Q3 budget is $500,000."
        prompt = self.agent.build_prompt("Show budget", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("Summarize expenses", "", user_role="CFO")
        assert "CFO" in prompt

    def test_prompt_defaults_to_analyst_role(self):
        prompt = self.agent.build_prompt("What is the revenue?", "")
        assert "analyst" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("Invoice details?", "")
        assert "No documents provided." in prompt


class TestFinanceAgentExtractCategories:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_extracts_budget(self):
        categories = self.agent.extract_categories("What is the current budget forecast?")
        assert "budget" in categories

    def test_extracts_invoice(self):
        categories = self.agent.extract_categories("Process the vendor invoice for payment")
        assert "invoice" in categories

    def test_extracts_revenue(self):
        categories = self.agent.extract_categories("Show me the revenue and profit trends")
        assert "revenue" in categories

    def test_extracts_multiple_categories(self):
        categories = self.agent.extract_categories("Budget review and expense reimbursement")
        assert "budget" in categories
        assert "expense" in categories

    def test_defaults_to_general_finance(self):
        categories = self.agent.extract_categories("Tell me something about the company")
        assert categories == ["general_finance"]


class TestFinanceAgentDetectAnomaly:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_detects_critical_anomaly(self):
        result = self.agent.detect_anomaly(actual=150_000, expected=100_000)
        assert result["has_anomaly"] is True
        assert result["severity"] == "critical"
        assert result["variance_pct"] == 50.0

    def test_detects_high_anomaly(self):
        result = self.agent.detect_anomaly(actual=125_000, expected=100_000)
        assert result["has_anomaly"] is True
        assert result["severity"] == "high"

    def test_no_anomaly_within_threshold(self):
        result = self.agent.detect_anomaly(actual=105_000, expected=100_000)
        assert result["has_anomaly"] is False
        assert result["severity"] == "none"

    def test_handles_zero_expected(self):
        result = self.agent.detect_anomaly(actual=50_000, expected=0)
        assert result["has_anomaly"] is False


class TestFinanceAgentFormatSummary:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_summary_contains_title(self):
        report = self.agent.format_summary("Q3 Expenses", [{"label": "Travel", "amount": 5000}])
        assert "Q3 Expenses" in report

    def test_summary_contains_line_items(self):
        report = self.agent.format_summary("Budget", [{"label": "Marketing", "amount": 20000}])
        assert "Marketing" in report
        assert "20,000.00" in report

    def test_summary_calculates_total(self):
        items = [{"label": "A", "amount": 1000}, {"label": "B", "amount": 2000}]
        report = self.agent.format_summary("Test", items)
        assert "3,000.00" in report

    def test_summary_handles_empty_items(self):
        report = self.agent.format_summary("Empty Report", [])
        assert "No financial data available." in report


class TestFinanceAgentCalculateVariance:
    def setup_method(self):
        self.agent = FinanceAgent()

    def test_over_budget(self):
        result = self.agent.calculate_variance(actual=120_000, budget=100_000)
        assert result["status"] == "over_budget"
        assert result["variance"] == 20_000
        assert result["variance_pct"] == 20.0

    def test_under_budget(self):
        result = self.agent.calculate_variance(actual=80_000, budget=100_000)
        assert result["status"] == "under_budget"
        assert result["variance"] == -20_000

    def test_on_budget(self):
        result = self.agent.calculate_variance(actual=100_000, budget=100_000)
        assert result["status"] == "on_budget"
        assert result["variance"] == 0

    def test_handles_zero_budget(self):
        result = self.agent.calculate_variance(actual=50_000, budget=0)
        assert result["variance_pct"] == 0.0
