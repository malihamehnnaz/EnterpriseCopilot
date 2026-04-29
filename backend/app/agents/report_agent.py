from datetime import datetime, timezone

REPORT_SYSTEM_PROMPT = """You are an expert Report Generation Agent for an enterprise organization.

Your responsibilities include:
- Creating executive summaries from raw AI agent outputs
- Formatting meeting summaries and action item lists
- Generating structured reports combining insights from multiple agents
- Producing professional documents suitable for management review

Always structure reports with clear headings, concise bullet points, and a summary section.
Highlight key findings, risks, and recommended actions prominently.
"""

_SECTION_ORDER = [
    "executive_summary",
    "key_findings",
    "risks",
    "recommendations",
    "action_items",
]


class ReportGenerationAgent:
    """
    Specialized agent for generating structured reports and executive summaries.
    Combines outputs from multiple agents into polished, readable documents.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "manager") -> str:
        """Build a structured prompt for the report generation agent."""
        return (
            f"{REPORT_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Report Request: {query}\n\n"
            f"Source Material:\n{context or 'No source material provided.'}\n\n"
            "Generate a professional, structured report with clear sections and action items:"
        )

    def generate_executive_summary(self, sections: dict[str, str], title: str = "Executive Summary") -> str:
        """
        Generate an executive summary document from a dict of named sections.
        Sections are ordered according to a standard report structure.
        """
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
        lines = [f"# {title}", f"*Generated: {date_str} (UTC)*\n"]

        # Write sections in standard order, then any extras
        ordered_keys = [k for k in _SECTION_ORDER if k in sections]
        extra_keys = [k for k in sections if k not in _SECTION_ORDER]

        for key in ordered_keys + extra_keys:
            heading = key.replace("_", " ").title()
            lines.append(f"## {heading}\n{sections[key]}\n")

        return "\n".join(lines)

    def format_action_items(self, items: list[dict]) -> str:
        """
        Format a list of action item dicts into a checklist.
        Each dict should have 'task', and optionally 'owner' and 'due_date'.
        """
        if not items:
            return "No action items identified."

        lines = ["## Action Items\n"]
        for i, item in enumerate(items, 1):
            task = item.get("task", "Unspecified task")
            owner = item.get("owner", "TBD")
            due = item.get("due_date", "TBD")
            lines.append(f"{i}. [ ] **{task}** — Owner: {owner} | Due: {due}")

        return "\n".join(lines)

    def combine_agent_outputs(self, outputs: dict[str, str]) -> str:
        """
        Combine outputs from multiple specialized agents into one consolidated report body.
        Keys are agent names, values are their text outputs.
        """
        if not outputs:
            return "No agent outputs to combine."

        lines = ["## Multi-Agent Analysis\n"]
        for agent_name, output in outputs.items():
            heading = agent_name.replace("_", " ").title()
            lines.append(f"### {heading} Agent\n{output}\n")

        return "\n".join(lines)

    def extract_action_items_from_text(self, text: str) -> list[str]:
        """
        Heuristically extract action items from free-form text.
        Looks for lines that contain action-oriented language.
        """
        action_triggers = [
            "should", "must", "need to", "action:", "todo:", "follow up",
            "ensure", "schedule", "review", "update", "send", "complete",
            "assign", "notify", "create", "submit",
        ]
        results = []
        for line in text.splitlines():
            lowered = line.lower().strip()
            if any(trigger in lowered for trigger in action_triggers) and len(lowered) > 10:
                results.append(line.strip())
        return results
