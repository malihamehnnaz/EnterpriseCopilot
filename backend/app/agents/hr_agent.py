HR_SYSTEM_PROMPT = """You are an expert HR Agent for an enterprise organization.

Your responsibilities include:
- Answering questions about HR policies, employee handbooks, and procedures
- Assisting with onboarding checklists and new hire workflows
- Clarifying payroll, benefits, leave, and compensation queries
- Summarizing recruitment and performance review processes

Always cite the source document and section when referencing policy.
If information is not available in the provided context, state that clearly.
"""

_TOPIC_KEYWORD_MAP: dict[str, list[str]] = {
    "onboarding": ["onboard", "new hire", "start date", "first day", "induction"],
    "payroll": ["payroll", "salary", "pay", "wage", "compensation", "bonus"],
    "leave": ["leave", "vacation", "pto", "time off", "sick day", "absence"],
    "recruitment": ["recruit", "hire", "job posting", "interview", "candidate", "offer letter"],
    "benefits": ["benefit", "health", "insurance", "pension", "401k", "perks"],
    "performance": ["performance", "review", "appraisal", "evaluation", "goal"],
    "termination": ["termination", "resign", "layoff", "exit", "separation"],
}


class HRAgent:
    """
    Specialized agent for Human Resources queries.
    Handles onboarding, payroll, leave, recruitment, and HR policies.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "employee") -> str:
        """Build a structured prompt for the HR agent."""
        return (
            f"{HR_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Question: {query}\n\n"
            f"Relevant HR Documents:\n{context or 'No documents provided.'}\n\n"
            "Provide a clear, policy-compliant answer with source citations:"
        )

    def extract_topics(self, query: str) -> list[str]:
        """
        Extract HR-relevant topics from a query for targeted retrieval.
        Returns a list of matched topic names.
        """
        lowered = query.lower()
        return [
            topic
            for topic, keywords in _TOPIC_KEYWORD_MAP.items()
            if any(kw in lowered for kw in keywords)
        ] or ["general_hr"]

    def generate_onboarding_checklist(self, employee_name: str, role: str) -> str:
        """Generate a standard onboarding checklist for a new employee."""
        return (
            f"## Onboarding Checklist for {employee_name} ({role})\n\n"
            "### Day 1\n"
            "- [ ] System access setup (email, Slack, VPN)\n"
            "- [ ] ID badge and office access\n"
            "- [ ] Introduction to team and manager\n"
            "- [ ] Review employee handbook\n\n"
            "### Week 1\n"
            "- [ ] Complete HR onboarding documents\n"
            "- [ ] Benefits enrollment\n"
            "- [ ] Role-specific training plan\n"
            "- [ ] Meet key stakeholders\n\n"
            "### Month 1\n"
            "- [ ] Complete mandatory compliance training\n"
            "- [ ] Set 30/60/90-day goals with manager\n"
            "- [ ] Payroll and direct deposit confirmation\n"
        )
