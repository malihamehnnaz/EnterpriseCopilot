import pytest
from backend.app.agents.compliance_agent import ComplianceAgent


class TestComplianceAgentBuildPrompt:
    def setup_method(self):
        self.agent = ComplianceAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("Check for GDPR issues", "Some contract text.")
        assert "Check for GDPR issues" in prompt

    def test_prompt_contains_context(self):
        context = "Contract lacks a data retention clause."
        prompt = self.agent.build_prompt("Review this contract", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("Audit the policy", "", user_role="auditor")
        assert "auditor" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("Any risks?", "")
        assert "No documents provided." in prompt


class TestComplianceAgentAssessRiskLevel:
    def setup_method(self):
        self.agent = ComplianceAgent()

    def test_detects_high_risk_gdpr(self):
        assert self.agent.assess_risk_level("This document violates GDPR regulations.") == "high"

    def test_detects_high_risk_breach(self):
        assert self.agent.assess_risk_level("There has been a data breach.") == "high"

    def test_detects_medium_risk_outdated(self):
        assert self.agent.assess_risk_level("The policy is outdated and needs review.") == "medium"

    def test_detects_low_risk_recommendation(self):
        assert self.agent.assess_risk_level("It is a recommendation to improve the process.") == "low"

    def test_defaults_to_low_when_no_match(self):
        assert self.agent.assess_risk_level("The meeting is at 3pm tomorrow.") == "low"

    def test_high_risk_takes_priority(self):
        # Text with both high and low keywords — should return high
        assert self.agent.assess_risk_level("Minor suggestion regarding GDPR violation") == "high"


class TestComplianceAgentFormatRiskReport:
    def setup_method(self):
        self.agent = ComplianceAgent()

    def test_returns_no_risks_message_when_empty(self):
        assert self.agent.format_risk_report([]) == "No compliance risks identified."

    def test_formats_single_risk(self):
        risks = [{"level": "high", "description": "Missing GDPR consent clause"}]
        report = self.agent.format_risk_report(risks)
        assert "[HIGH]" in report
        assert "Missing GDPR consent clause" in report

    def test_formats_multiple_risks(self):
        risks = [
            {"level": "high", "description": "Data breach risk"},
            {"level": "medium", "description": "Outdated privacy policy"},
        ]
        report = self.agent.format_risk_report(risks)
        assert "1." in report
        assert "2." in report
        assert "[HIGH]" in report
        assert "[MEDIUM]" in report

    def test_handles_missing_level_key(self):
        risks = [{"description": "Some risk"}]
        report = self.agent.format_risk_report(risks)
        assert "[LOW]" in report

    def test_report_has_header(self):
        risks = [{"level": "low", "description": "Minor issue"}]
        report = self.agent.format_risk_report(risks)
        assert "Compliance Risk Report" in report


class TestComplianceAgentExtractRegulations:
    def setup_method(self):
        self.agent = ComplianceAgent()

    def test_extracts_gdpr(self):
        regs = self.agent.extract_regulations("This contract must comply with GDPR.")
        assert "GDPR" in regs

    def test_extracts_multiple_regulations(self):
        regs = self.agent.extract_regulations("Ensure HIPAA and SOX compliance in this document.")
        assert "HIPAA" in regs
        assert "SOX" in regs

    def test_returns_empty_when_no_regulations(self):
        regs = self.agent.extract_regulations("The meeting starts at 10am.")
        assert regs == []

    def test_case_insensitive_detection(self):
        regs = self.agent.extract_regulations("must follow gdpr and hipaa guidelines")
        assert "GDPR" in regs
        assert "HIPAA" in regs
