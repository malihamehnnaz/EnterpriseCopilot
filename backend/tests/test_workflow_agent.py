import pytest
from backend.app.agents.workflow_agent import WorkflowAgent, WorkflowTask


class TestWorkflowAgentBuildPrompt:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_prompt_contains_query(self):
        prompt = self.agent.build_prompt("Onboard new hire Alice", "HR docs context.")
        assert "Onboard new hire Alice" in prompt

    def test_prompt_contains_context(self):
        context = "Alice starts Monday as a Software Engineer."
        prompt = self.agent.build_prompt("Create onboarding plan", context)
        assert context in prompt

    def test_prompt_contains_user_role(self):
        prompt = self.agent.build_prompt("Setup approvals", "", user_role="HR Director")
        assert "HR Director" in prompt

    def test_prompt_defaults_to_manager_role(self):
        prompt = self.agent.build_prompt("Schedule tasks", "")
        assert "manager" in prompt

    def test_prompt_handles_empty_context(self):
        prompt = self.agent.build_prompt("Plan workflow", "")
        assert "No context provided." in prompt


class TestWorkflowAgentRequiresApproval:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_hire_requires_approval(self):
        assert self.agent.requires_approval("We need to hire a new engineer") is True

    def test_terminate_requires_approval(self):
        assert self.agent.requires_approval("Terminate the employee contract") is True

    def test_budget_approval_requires_approval(self):
        assert self.agent.requires_approval("This requires budget approval from finance") is True

    def test_general_task_no_approval(self):
        assert self.agent.requires_approval("Schedule a team standup for Monday") is False

    def test_case_insensitive(self):
        assert self.agent.requires_approval("FINANCIAL APPROVAL needed for Q3 spend") is True

    def test_contract_sign_requires_approval(self):
        assert self.agent.requires_approval("Please contract sign the vendor agreement") is True


class TestWorkflowAgentBuildApprovalRequest:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_approval_request_contains_task(self):
        request = self.agent.build_approval_request("Hire senior engineer", "Alice", "Team expansion")
        assert "Hire senior engineer" in request

    def test_approval_request_contains_requester(self):
        request = self.agent.build_approval_request("Approve budget", "Bob", "Q3 planning")
        assert "Bob" in request

    def test_approval_request_contains_approver(self):
        request = self.agent.build_approval_request("Grant access", "Carol", "Project need", approver="CTO")
        assert "CTO" in request

    def test_approval_request_defaults_manager_approver(self):
        request = self.agent.build_approval_request("Terminate contract", "Dave", "Performance issues")
        assert "Manager" in request

    def test_approval_request_has_checkboxes(self):
        request = self.agent.build_approval_request("Policy exception", "Eve", "Urgent need")
        assert "Approved" in request
        assert "Rejected" in request

    def test_approval_request_has_date(self):
        request = self.agent.build_approval_request("Data export", "Frank", "Analytics need")
        assert "2026" in request


class TestWorkflowAgentBuildNotification:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_notification_contains_event(self):
        note = self.agent.build_notification("Onboarding Started", ["hr@company.com"], "Alice has started onboarding.")
        assert "Onboarding Started" in note

    def test_notification_contains_body(self):
        body = "The quarterly audit has been completed successfully."
        note = self.agent.build_notification("Audit Complete", ["cfo@company.com"], body)
        assert body in note

    def test_notification_contains_recipients(self):
        note = self.agent.build_notification("Policy Update", ["alice@co.com", "bob@co.com"], "Policy changed.")
        assert "alice@co.com" in note
        assert "bob@co.com" in note

    def test_notification_defaults_all_stakeholders_when_empty(self):
        note = self.agent.build_notification("System Update", [], "Maintenance tonight.")
        assert "All Stakeholders" in note

    def test_notification_has_date(self):
        note = self.agent.build_notification("Report Ready", ["mgr@co.com"], "Report is ready.")
        assert "2026" in note


class TestWorkflowAgentCreatePlan:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_plan_contains_goal(self):
        plan = self.agent.create_workflow_plan("Onboard Alice", [])
        assert "Onboard Alice" in plan

    def test_plan_handles_empty_tasks(self):
        plan = self.agent.create_workflow_plan("Empty Goal", [])
        assert "No tasks defined." in plan

    def test_plan_contains_task_title(self):
        tasks = [WorkflowTask(title="Setup email account", owner="IT")]
        plan = self.agent.create_workflow_plan("IT Setup", tasks)
        assert "Setup email account" in plan

    def test_plan_shows_approval_flag(self):
        tasks = [WorkflowTask(title="Contract sign", requires_approval=True)]
        plan = self.agent.create_workflow_plan("Legal", tasks)
        assert "Requires Approval" in plan

    def test_plan_shows_total_count(self):
        tasks = [WorkflowTask("Task A"), WorkflowTask("Task B")]
        plan = self.agent.create_workflow_plan("Test Plan", tasks)
        assert "**Total tasks:** 2" in plan

    def test_plan_shows_approval_count(self):
        tasks = [
            WorkflowTask("Task A", requires_approval=True),
            WorkflowTask("Task B", requires_approval=False),
        ]
        plan = self.agent.create_workflow_plan("Mixed", tasks)
        assert "**Requires approval:** 1" in plan


class TestWorkflowAgentSequenceTasks:
    def setup_method(self):
        self.agent = WorkflowAgent()

    def test_critical_first(self):
        tasks = [
            WorkflowTask("Low task", priority="low"),
            WorkflowTask("Critical task", priority="critical"),
        ]
        ordered = self.agent.sequence_tasks(tasks)
        assert ordered[0].title == "Critical task"

    def test_approval_tasks_before_non_approval_same_priority(self):
        tasks = [
            WorkflowTask("Normal high", priority="high", requires_approval=False),
            WorkflowTask("Approval high", priority="high", requires_approval=True),
        ]
        ordered = self.agent.sequence_tasks(tasks)
        assert ordered[0].title == "Approval high"

    def test_all_priorities_ordered(self):
        tasks = [
            WorkflowTask("Low", priority="low"),
            WorkflowTask("High", priority="high"),
            WorkflowTask("Medium", priority="medium"),
            WorkflowTask("Critical", priority="critical"),
        ]
        ordered = self.agent.sequence_tasks(tasks)
        priorities = [t.priority for t in ordered]
        assert priorities == ["critical", "high", "medium", "low"]

    def test_empty_list_returns_empty(self):
        assert self.agent.sequence_tasks([]) == []


class TestWorkflowTask:
    def test_default_status_is_pending(self):
        task = WorkflowTask("Do something")
        assert task.status == "pending"

    def test_to_dict_has_all_keys(self):
        task = WorkflowTask("Test task", owner="Alice", priority="high")
        d = task.to_dict()
        assert "title" in d
        assert "owner" in d
        assert "priority" in d
        assert "due_date" in d
        assert "depends_on" in d
        assert "requires_approval" in d
        assert "status" in d

    def test_depends_on_defaults_empty(self):
        task = WorkflowTask("Standalone task")
        assert task.depends_on == []
