import pytest
from backend.app.agents.orchestrator import OrchestratorAgent, classify_query


class TestClassifyQuery:
    def test_routes_hr_keywords(self):
        assert classify_query("What is the onboarding process for new employees?") == "hr"

    def test_routes_finance_keywords(self):
        assert classify_query("Show me the budget forecast for this quarter") == "finance"

    def test_routes_compliance_keywords(self):
        assert classify_query("Are there any GDPR violations in this contract?") == "compliance"

    def test_routes_analytics_keywords(self):
        assert classify_query("What are the KPI trends from the last report?") == "analytics"

    def test_falls_back_to_general(self):
        assert classify_query("Hello, how are you?") == "general"

    def test_case_insensitive(self):
        assert classify_query("PAYROLL REVIEW FOR EMPLOYEES") == "hr"

    def test_highest_score_wins(self):
        # "audit" → compliance, "payroll" → hr — compliance has more keywords here
        result = classify_query("audit the compliance policy")
        assert result == "compliance"


class TestOrchestratorAgent:
    def setup_method(self):
        self.agent = OrchestratorAgent()

    def test_route_returns_dict_with_required_keys(self):
        result = self.agent.route("What is the leave policy?")
        assert "active_agent" in result
        assert "agent_description" in result

    def test_route_hr_query(self):
        result = self.agent.route("Tell me about employee benefits and payroll")
        assert result["active_agent"] == "hr"

    def test_route_compliance_query(self):
        result = self.agent.route("Check the contract for GDPR compliance violations")
        assert result["active_agent"] == "compliance"

    def test_route_general_query(self):
        result = self.agent.route("What is the weather today?")
        assert result["active_agent"] == "general"

    def test_agent_description_is_non_empty(self):
        for query in [
            "payroll information",
            "invoice budget",
            "GDPR audit",
            "KPI trends",
            "random query",
        ]:
            result = self.agent.route(query)
            assert result["agent_description"]

    def test_all_agent_types_have_descriptions(self):
        for agent_type in OrchestratorAgent.AGENT_DESCRIPTIONS:
            assert OrchestratorAgent.AGENT_DESCRIPTIONS[agent_type]
