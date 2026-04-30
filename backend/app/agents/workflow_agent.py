from datetime import datetime, timezone
from typing import Literal

TaskStatus = Literal["pending", "in_progress", "completed", "blocked", "cancelled"]
Priority = Literal["low", "medium", "high", "critical"]

WORKFLOW_SYSTEM_PROMPT = """You are an expert Workflow Automation Agent for an enterprise organization.

Your responsibilities include:
- Breaking complex requests into structured, ordered task plans
- Generating approval request templates for management sign-off
- Creating notification messages for relevant stakeholders
- Identifying task dependencies and sequencing steps correctly
- Flagging tasks that require human approval before proceeding

Always output clear, actionable steps with owners, priorities, and deadlines.
"""

_APPROVAL_REQUIRED_TRIGGERS = [
    "hire", "terminate", "layoff", "budget approval", "contract sign",
    "policy change", "access grant", "data export", "financial approval",
    "compliance waiver", "exception", "override",
]


class WorkflowTask:
    """Represents a single task within a workflow plan."""

    def __init__(
        self,
        title: str,
        owner: str = "TBD",
        priority: Priority = "medium",
        due_date: str = "TBD",
        depends_on: list[str] | None = None,
        requires_approval: bool = False,
    ) -> None:
        self.title = title
        self.owner = owner
        self.priority = priority
        self.due_date = due_date
        self.depends_on: list[str] = depends_on or []
        self.requires_approval = requires_approval
        self.status: TaskStatus = "pending"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "owner": self.owner,
            "priority": self.priority,
            "due_date": self.due_date,
            "depends_on": self.depends_on,
            "requires_approval": self.requires_approval,
            "status": self.status,
        }


class WorkflowAgent:
    """
    Specialized agent for workflow automation and task orchestration.
    Generates task plans, approval requests, and notification templates.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "manager") -> str:
        """Build a structured prompt for the workflow agent."""
        return (
            f"{WORKFLOW_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Request: {query}\n\n"
            f"Context / Documents:\n{context or 'No context provided.'}\n\n"
            "Generate a structured workflow plan with tasks, owners, priorities, and approval steps:"
        )

    def requires_approval(self, query: str) -> bool:
        """
        Determine whether a workflow request requires management approval.
        Returns True if any approval-trigger keywords are present.
        """
        lowered = query.lower()
        return any(trigger in lowered for trigger in _APPROVAL_REQUIRED_TRIGGERS)

    def build_approval_request(self, task: str, requester: str, reason: str, approver: str = "Manager") -> str:
        """
        Generate a formal approval request message.
        """
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        return (
            f"## Approval Request\n\n"
            f"**Date:** {date_str} (UTC)\n"
            f"**Requester:** {requester}\n"
            f"**Approver:** {approver}\n\n"
            f"**Task:** {task}\n\n"
            f"**Reason / Justification:**\n{reason}\n\n"
            f"**Action Required:** Please review and approve or reject this request.\n"
            f"- [ ] Approved\n"
            f"- [ ] Rejected\n"
            f"- [ ] Request More Information\n"
        )

    def build_notification(self, event: str, recipients: list[str], body: str) -> str:
        """
        Generate a stakeholder notification message for a workflow event.
        """
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        recipient_list = ", ".join(recipients) if recipients else "All Stakeholders"
        return (
            f"## Notification: {event}\n\n"
            f"**Date:** {date_str} (UTC)\n"
            f"**To:** {recipient_list}\n\n"
            f"{body}\n\n"
            f"*This is an automated notification from the Enterprise Copilot system.*"
        )

    def create_workflow_plan(self, goal: str, tasks: list[WorkflowTask]) -> str:
        """
        Format a list of WorkflowTask objects into a readable plan.
        """
        if not tasks:
            return f"## Workflow Plan: {goal}\n\nNo tasks defined."

        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        lines = [f"## Workflow Plan: {goal}", f"*Created: {date_str} (UTC)*\n"]

        for i, task in enumerate(tasks, 1):
            approval_flag = " 🔒 *Requires Approval*" if task.requires_approval else ""
            priority_tag = f"[{task.priority.upper()}]"
            lines.append(f"{i}. {priority_tag} **{task.title}**{approval_flag}")
            lines.append(f"   - Owner: {task.owner}")
            lines.append(f"   - Due: {task.due_date}")
            lines.append(f"   - Status: {task.status}")
            if task.depends_on:
                deps = ", ".join(f"Task {d}" for d in task.depends_on)
                lines.append(f"   - Depends on: {deps}")

        approval_count = sum(1 for t in tasks if t.requires_approval)
        lines.append(f"\n**Total tasks:** {len(tasks)} | **Requires approval:** {approval_count}")
        return "\n".join(lines)

    def sequence_tasks(self, tasks: list[WorkflowTask]) -> list[WorkflowTask]:
        """
        Return tasks sorted by priority (critical → high → medium → low),
        with approval-required tasks listed before non-approval tasks of same priority.
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(
            tasks,
            key=lambda t: (priority_order.get(t.priority, 2), not t.requires_approval),
        )
