import pytest
from backend.app.agents.hr_agent import HRAgent


class TestHRAgentBuildPrompt:
    def setup_method(self):
        self.agent = HRAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("What is the leave policy?", "Leave policy context.")
        assert "What is the leave policy?" in prompt

    def test_prompt_contains_context(self):
        context = "Employees get 20 days of annual leave."
        prompt = self.agent.build_prompt("How many days off?", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("What is my salary?", "", user_role="manager")
        assert "manager" in prompt

    def test_prompt_defaults_to_employee_role(self):
        prompt = self.agent.build_prompt("What is the bonus policy?", "")
        assert "employee" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("What is the PTO policy?", "")
        assert "No documents provided." in prompt


class TestHRAgentExtractTopics:
    def setup_method(self):
        self.agent = HRAgent()

    def test_extracts_onboarding(self):
        topics = self.agent.extract_topics("What is the onboarding process?")
        assert "onboarding" in topics

    def test_extracts_payroll(self):
        topics = self.agent.extract_topics("When is the next payroll date?")
        assert "payroll" in topics

    def test_extracts_leave(self):
        topics = self.agent.extract_topics("How do I apply for PTO?")
        assert "leave" in topics

    def test_extracts_multiple_topics(self):
        topics = self.agent.extract_topics("What is the payroll and benefits policy?")
        assert "payroll" in topics
        assert "benefits" in topics

    def test_defaults_to_general_hr(self):
        topics = self.agent.extract_topics("Tell me something about the company")
        assert topics == ["general_hr"]


class TestHRAgentOnboardingChecklist:
    def setup_method(self):
        self.agent = HRAgent()

    def test_checklist_contains_employee_name(self):
        checklist = self.agent.generate_onboarding_checklist("Alice", "Engineer")
        assert "Alice" in checklist

    def test_checklist_contains_role(self):
        checklist = self.agent.generate_onboarding_checklist("Bob", "Product Manager")
        assert "Product Manager" in checklist

    def test_checklist_has_day1_section(self):
        checklist = self.agent.generate_onboarding_checklist("Carol", "Analyst")
        assert "Day 1" in checklist

    def test_checklist_has_month1_section(self):
        checklist = self.agent.generate_onboarding_checklist("Dave", "Designer")
        assert "Month 1" in checklist
