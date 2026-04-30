import sys
import uuid
from unittest.mock import MagicMock

# Stub out DB dependencies before importing the service under test so
# tests can run without asyncpg / a live database.
_mock_session = MagicMock()
_mock_models = MagicMock()
sys.modules.setdefault("app.db.session", _mock_session)
sys.modules.setdefault("app.db.models", _mock_models)

from backend.app.services.observability_service import (  # noqa: E402
    build_agent_execution_record,
    build_notification_record,
    build_query_record,
    build_workflow_record,
    compute_dashboard_stats,
    ObservabilityService,
)


# ---------------------------------------------------------------------------
# Helper to build a minimal TokenUsage-like object
# ---------------------------------------------------------------------------

class FakeTokenUsage:
    prompt_tokens = 100
    completion_tokens = 50
    total_tokens = 150


class FakeSourceItem:
    def model_dump(self):
        return {"source": "test_doc.pdf", "page": 1}


# ---------------------------------------------------------------------------
# build_query_record
# ---------------------------------------------------------------------------

class TestBuildQueryRecord:
    def _make(self, **overrides):
        defaults = dict(
            user_id="user_1",
            session_id="sess_abc",
            role="employee",
            request_type="qa",
            active_agent="hr",
            query_text="What is the leave policy?",
            response_text="You get 20 days.",
            model_name="gpt-4",
            token_usage=FakeTokenUsage(),
            sources=[FakeSourceItem()],
            latency_ms=312,
            validation_result="passed",
        )
        defaults.update(overrides)
        return build_query_record(**defaults)

    def test_contains_user_id(self):
        r = self._make()
        assert r["user_id"] == "user_1"

    def test_contains_session_id(self):
        r = self._make()
        assert r["session_id"] == "sess_abc"

    def test_contains_active_agent(self):
        r = self._make()
        assert r["active_agent"] == "hr"

    def test_contains_latency_ms(self):
        r = self._make()
        assert r["latency_ms"] == 312

    def test_contains_validation_result(self):
        r = self._make()
        assert r["validation_result"] == "passed"

    def test_contains_token_fields(self):
        r = self._make()
        assert r["prompt_tokens"] == 100
        assert r["completion_tokens"] == 50
        assert r["total_tokens"] == 150

    def test_source_payload_structure(self):
        r = self._make()
        assert "sources" in r["source_payload"]
        assert isinstance(r["source_payload"]["sources"], list)

    def test_handles_none_session_id(self):
        r = self._make(session_id=None)
        assert r["session_id"] is None

    def test_handles_none_validation_result(self):
        r = self._make(validation_result=None)
        assert r["validation_result"] is None


# ---------------------------------------------------------------------------
# build_agent_execution_record
# ---------------------------------------------------------------------------

class TestBuildAgentExecutionRecord:
    def _make(self, **overrides):
        defaults = dict(
            agent_name="compliance",
            user_id="user_2",
            input_text="Check for GDPR issues in this contract.",
            output_text="Found 2 high-risk GDPR violations.",
            latency_ms=220,
            token_count=80,
            success=True,
        )
        defaults.update(overrides)
        return build_agent_execution_record(**defaults)

    def test_contains_agent_name(self):
        r = self._make()
        assert r["agent_name"] == "compliance"

    def test_input_preview_truncated_to_500(self):
        long_input = "x" * 1000
        r = self._make(input_text=long_input)
        assert len(r["input_preview"]) == 500

    def test_output_preview_truncated_to_500(self):
        long_output = "y" * 1000
        r = self._make(output_text=long_output)
        assert len(r["output_preview"]) == 500

    def test_contains_latency(self):
        r = self._make()
        assert r["latency_ms"] == 220

    def test_success_true_by_default(self):
        r = self._make()
        assert r["success"] is True

    def test_failed_execution(self):
        r = self._make(success=False, error_message="Timeout")
        assert r["success"] is False
        assert r["error_message"] == "Timeout"

    def test_query_log_id_can_be_set(self):
        qid = uuid.uuid4()
        r = self._make(query_log_id=qid)
        assert r["query_log_id"] == qid

    def test_query_log_id_defaults_none(self):
        r = self._make()
        assert r["query_log_id"] is None


# ---------------------------------------------------------------------------
# build_workflow_record
# ---------------------------------------------------------------------------

class TestBuildWorkflowRecord:
    def _make(self, **overrides):
        defaults = dict(
            user_id="user_3",
            goal="Onboard Alice",
            tasks=[{"title": "Setup email"}, {"title": "ID badge"}],
            requires_approval=False,
        )
        defaults.update(overrides)
        return build_workflow_record(**defaults)

    def test_contains_goal(self):
        r = self._make()
        assert r["goal"] == "Onboard Alice"

    def test_tasks_stored_in_json(self):
        r = self._make()
        assert "tasks" in r["tasks_json"]
        assert len(r["tasks_json"]["tasks"]) == 2

    def test_no_approval_status(self):
        r = self._make(requires_approval=False)
        assert r["approval_status"] == "not_required"

    def test_pending_when_approval_required(self):
        r = self._make(requires_approval=True)
        assert r["approval_status"] == "pending"
        assert r["requires_approval"] is True


# ---------------------------------------------------------------------------
# build_notification_record
# ---------------------------------------------------------------------------

class TestBuildNotificationRecord:
    def _make(self, **overrides):
        defaults = dict(
            user_id="user_4",
            event_name="Onboarding Started",
            recipients=["hr@company.com", "mgr@company.com"],
            body="Alice has started her onboarding process.",
        )
        defaults.update(overrides)
        return build_notification_record(**defaults)

    def test_contains_event_name(self):
        r = self._make()
        assert r["event_name"] == "Onboarding Started"

    def test_recipients_stored_in_json(self):
        r = self._make()
        assert "recipients" in r["recipients_json"]
        assert "hr@company.com" in r["recipients_json"]["recipients"]

    def test_delivered_defaults_false(self):
        r = self._make()
        assert r["delivered"] is False

    def test_empty_recipients(self):
        r = self._make(recipients=[])
        assert r["recipients_json"]["recipients"] == []


# ---------------------------------------------------------------------------
# compute_dashboard_stats
# ---------------------------------------------------------------------------

class TestComputeDashboardStats:
    def _records(self):
        return [
            {"latency_ms": 200, "total_tokens": 100, "active_agent": "hr", "model_name": "gpt-4"},
            {"latency_ms": 400, "total_tokens": 200, "active_agent": "compliance", "model_name": "gpt-4"},
            {"latency_ms": 600, "total_tokens": 300, "active_agent": "hr", "model_name": "gpt-3.5"},
            {"latency_ms": 100, "total_tokens": 50, "active_agent": "general", "model_name": "gpt-3.5"},
        ]

    def test_total_queries(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["total_queries"] == 4

    def test_avg_latency(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["avg_latency_ms"] == 325.0

    def test_total_tokens(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["total_tokens"] == 650

    def test_avg_tokens(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["avg_tokens"] == 162.5

    def test_agent_distribution(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["agent_distribution"]["hr"] == 2
        assert stats["agent_distribution"]["compliance"] == 1

    def test_model_distribution(self):
        stats = compute_dashboard_stats(self._records())
        assert stats["model_distribution"]["gpt-4"] == 2
        assert stats["model_distribution"]["gpt-3.5"] == 2

    def test_p95_latency(self):
        stats = compute_dashboard_stats(self._records())
        # 4 records, p95 index = max(0, int(4*0.95)-1) = max(0, 2) = 2
        # sorted latencies: [100, 200, 400, 600] → index 2 = 400
        assert stats["p95_latency_ms"] == 400.0

    def test_empty_records_returns_zeros(self):
        stats = compute_dashboard_stats([])
        assert stats["total_queries"] == 0
        assert stats["avg_latency_ms"] == 0.0
        assert stats["total_tokens"] == 0

    def test_single_record(self):
        records = [{"latency_ms": 500, "total_tokens": 120, "active_agent": "finance", "model_name": "gpt-4"}]
        stats = compute_dashboard_stats(records)
        assert stats["total_queries"] == 1
        assert stats["avg_latency_ms"] == 500.0
        assert stats["p95_latency_ms"] == 500.0

    def test_missing_fields_default_to_zero_or_unknown(self):
        records = [{}]
        stats = compute_dashboard_stats(records)
        assert stats["total_queries"] == 1
        assert stats["agent_distribution"].get("unknown", 0) == 1
