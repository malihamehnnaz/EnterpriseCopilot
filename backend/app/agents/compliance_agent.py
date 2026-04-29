COMPLIANCE_SYSTEM_PROMPT = """You are an expert Compliance Agent for an enterprise organization.

Your responsibilities include:
- Identifying policy violations and missing compliance clauses
- Flagging potential regulatory risks (GDPR, HIPAA, SOX, CCPA, etc.)
- Reviewing contracts for incomplete or non-standard terms
- Generating audit-ready risk summaries

Always be specific about the type of risk and cite the relevant regulation or policy section.
Rate each identified risk as: LOW, MEDIUM, or HIGH.
"""

_RISK_LEVELS: dict[str, set[str]] = {
    "high": {
        "gdpr", "hipaa", "sox", "violation", "breach", "illegal",
        "fraud", "criminal", "data leak", "unauthorized", "ccpa",
    },
    "medium": {
        "missing clause", "non-compliant", "outdated", "unverified",
        "unclear", "ambiguous", "expired", "incomplete", "undocumented",
    },
    "low": {
        "recommendation", "best practice", "consider", "optional",
        "minor", "suggestion", "improvement", "review",
    },
}


class ComplianceAgent:
    """
    Specialized agent for compliance, risk assessment, and policy checking.
    Handles regulatory risks, contract analysis, and audit preparation.
    """

    def build_prompt(self, query: str, context: str, user_role: str = "employee") -> str:
        """Build a structured prompt for the compliance agent."""
        return (
            f"{COMPLIANCE_SYSTEM_PROMPT}\n"
            f"User Role: {user_role}\n"
            f"Query: {query}\n\n"
            f"Document Context:\n{context or 'No documents provided.'}\n\n"
            "Identify all compliance risks and provide a structured risk summary:"
        )

    def assess_risk_level(self, text: str) -> str:
        """
        Assess the risk level of a given text based on compliance keywords.
        Returns 'high', 'medium', or 'low'.
        """
        lowered = text.lower()
        for level in ("high", "medium", "low"):
            if any(kw in lowered for kw in _RISK_LEVELS[level]):
                return level
        return "low"

    def format_risk_report(self, risks: list[dict]) -> str:
        """
        Format a list of risk dicts into a readable compliance report.
        Each risk dict should have 'level' and 'description' keys.
        """
        if not risks:
            return "No compliance risks identified."
        lines = ["## Compliance Risk Report\n"]
        for i, risk in enumerate(risks, 1):
            level = risk.get("level", "LOW").upper()
            description = risk.get("description", "No description provided.")
            lines.append(f"{i}. [{level}] {description}")
        return "\n".join(lines)

    def extract_regulations(self, text: str) -> list[str]:
        """
        Extract mentions of specific regulations or standards from text.
        Returns a list of detected regulation names.
        """
        regulations = ["GDPR", "HIPAA", "SOX", "CCPA", "PCI-DSS", "ISO 27001", "NIST"]
        lowered = text.lower()
        return [reg for reg in regulations if reg.lower() in lowered]
