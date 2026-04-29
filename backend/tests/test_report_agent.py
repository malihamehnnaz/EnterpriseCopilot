import pytest
from backend.app.agents.report_agent import ReportGenerationAgent


class TestReportAgentBuildPrompt:
    def setup_method(self):
        self.agent = ReportGenerationAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("Generate onboarding report", "HR context.")
        assert "Generate onboarding report" in prompt

    def test_prompt_contains_context(self):
        context = "New hire Alice joined on Monday."
        prompt = self.agent.build_prompt("Summarize onboarding", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("Executive summary", "", user_role="director")
        assert "director" in prompt

    def test_prompt_defaults_to_manager_role(self):
        prompt = self.agent.build_prompt("Report please", "")
        assert "manager" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("Any insights?", "")
        assert "No source material provided." in prompt


class TestReportAgentExecutiveSummary:
    def setup_method(self):
        self.agent = ReportGenerationAgent()

    def test_summary_contains_title(self):
        report = self.agent.generate_executive_summary({}, title="Q3 Review")
        assert "Q3 Review" in report

    def test_summary_contains_section_headings(self):
        sections = {"key_findings": "Revenue grew 20%.", "risks": "Supply chain delays."}
        report = self.agent.generate_executive_summary(sections)
        assert "Key Findings" in report
        assert "Risks" in report

    def test_summary_contains_section_content(self):
        sections = {"executive_summary": "Strong performance this quarter."}
        report = self.agent.generate_executive_summary(sections)
        assert "Strong performance this quarter." in report

    def test_summary_has_date(self):
        report = self.agent.generate_executive_summary({}, title="Test")
        # Date is present — just check the year is there
        assert "2026" in report

    def test_extra_sections_appended(self):
        sections = {"custom_section": "Some custom content."}
        report = self.agent.generate_executive_summary(sections)
        assert "Custom Section" in report


class TestReportAgentFormatActionItems:
    def setup_method(self):
        self.agent = ReportGenerationAgent()

    def test_action_items_has_header(self):
        items = [{"task": "Update policy", "owner": "HR", "due_date": "2026-05-01"}]
        report = self.agent.format_action_items(items)
        assert "Action Items" in report

    def test_action_items_contains_task(self):
        items = [{"task": "Review contract", "owner": "Legal", "due_date": "2026-06-01"}]
        report = self.agent.format_action_items(items)
        assert "Review contract" in report

    def test_action_items_contains_owner(self):
        items = [{"task": "Audit logs", "owner": "IT", "due_date": "TBD"}]
        report = self.agent.format_action_items(items)
        assert "IT" in report

    def test_action_items_defaults_tbd_when_missing(self):
        items = [{"task": "Fix issue"}]
        report = self.agent.format_action_items(items)
        assert "TBD" in report

    def test_handles_empty_items(self):
        assert self.agent.format_action_items([]) == "No action items identified."

    def test_multiple_items_numbered(self):
        items = [{"task": "Task A"}, {"task": "Task B"}]
        report = self.agent.format_action_items(items)
        assert "1." in report
        assert "2." in report


class TestReportAgentCombineOutputs:
    def setup_method(self):
        self.agent = ReportGenerationAgent()

    def test_combined_report_has_header(self):
        outputs = {"hr_agent": "Onboarding complete."}
        report = self.agent.combine_agent_outputs(outputs)
        assert "Multi-Agent Analysis" in report

    def test_combined_report_contains_agent_output(self):
        outputs = {"compliance_agent": "No violations found."}
        report = self.agent.combine_agent_outputs(outputs)
        assert "No violations found." in report

    def test_combined_report_formats_agent_name(self):
        outputs = {"finance_agent": "Budget on track."}
        report = self.agent.combine_agent_outputs(outputs)
        assert "Finance Agent" in report

    def test_handles_empty_outputs(self):
        assert self.agent.combine_agent_outputs({}) == "No agent outputs to combine."


class TestReportAgentExtractActionItems:
    def setup_method(self):
        self.agent = ReportGenerationAgent()

    def test_extracts_should_statement(self):
        text = "The team should update the compliance policy by Friday."
        items = self.agent.extract_action_items_from_text(text)
        assert len(items) == 1
        assert "should update" in items[0]

    def test_extracts_must_statement(self):
        text = "All employees must complete the training by end of month."
        items = self.agent.extract_action_items_from_text(text)
        assert len(items) >= 1

    def test_ignores_short_lines(self):
        text = "review\nshould\nmust"
        items = self.agent.extract_action_items_from_text(text)
        assert items == []

    def test_extracts_multiple_items(self):
        text = (
            "We need to schedule a meeting with the board.\n"
            "The manager should review the report.\n"
            "This is an unrelated sentence."
        )
        items = self.agent.extract_action_items_from_text(text)
        assert len(items) == 2
