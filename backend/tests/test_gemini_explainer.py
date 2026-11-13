
from datetime import datetime, timezone

import pytest

from app.models.lead import LeadRecord
from app.services.context_builder import ContextBuilder
from app.services.explanation_service import ExplanationService
from app.services.gemini_explainer import GeminiExplainer


@pytest.fixture
def workflow_context():
    lead = LeadRecord(
        lead_id="LEAD-GEMINI-001",
        source="Website",
        created_at=datetime(2026, 11, 10, tzinfo=timezone.utc),
        last_contact_at=datetime(2026, 11, 12, tzinfo=timezone.utc),
        declared_need="Enterprise software",
        stage="Qualified",
        contact_available=True,
        pending_follow_up=True,
    )

    context = ContextBuilder.build(lead)

    context.final_recommendation = {
        "action": "FOLLOW_UP_NOW",
        "priority_score": 95,
        "triggered_rules": ["OVERDUE_FOLLOW_UP"],
        "reasons": ["Follow-up is overdue"],
    }

    ExplanationService.build(context)

    return context
from types import SimpleNamespace


def test_gemini_success_returns_valid_summary(
    workflow_context,
    monkeypatch,
):
    expected_summary = (
        "LEAD-GEMINI-001 receives FOLLOW_UP_NOW "
        "with a priority score of 95/100."
    )

    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            return SimpleNamespace(text=expected_summary)

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "completed"
    assert result["provider"] == "gemini"
    assert result["summary"] == expected_summary
    assert result["reason"] == "none"
def test_gemini_provider_error_uses_deterministic_fallback(
    workflow_context,
    monkeypatch,
):
    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            raise RuntimeError("Simulated provider failure")

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    original_summary = workflow_context.explanation["summary"]

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "fallback"
    assert result["reason"] == "provider_error"
    assert result["summary"] == original_summary
    assert workflow_context.final_recommendation["action"] == "FOLLOW_UP_NOW"
    assert workflow_context.final_recommendation["priority_score"] == 95
def test_gemini_timeout_uses_deterministic_fallback(
    workflow_context,
    monkeypatch,
):
    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            raise TimeoutError("Simulated Gemini timeout")

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    original_summary = workflow_context.explanation["summary"]

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "fallback"
    assert result["reason"] == "timeout"
    assert result["summary"] == original_summary
    assert workflow_context.final_recommendation["action"] == "FOLLOW_UP_NOW"
    assert workflow_context.final_recommendation["priority_score"] == 95
def test_gemini_invalid_response_uses_deterministic_fallback(
    workflow_context,
    monkeypatch,
):
    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            return SimpleNamespace(
                text="This lead may be worth reviewing."
            )

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    original_summary = workflow_context.explanation["summary"]

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "fallback"
    assert result["reason"] == "invalid_response"
    assert result["summary"] == original_summary
    assert workflow_context.final_recommendation["action"] == "FOLLOW_UP_NOW"
    assert workflow_context.final_recommendation["priority_score"] == 95
def test_gemini_missing_configuration_uses_fallback(
    workflow_context,
    monkeypatch,
):
    def unexpected_client_call(**kwargs):
        raise AssertionError(
            "Gemini client should not be created when unconfigured"
        )

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        unexpected_client_call,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: False),
    )

    original_summary = workflow_context.explanation["summary"]

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "fallback"
    assert result["reason"] == "not_configured"
    assert result["summary"] == original_summary
def test_gemini_prompt_excludes_lead_identifier(
    workflow_context,
    monkeypatch,
):
    captured_prompt = {}

    expected_summary = (
        "FOLLOW_UP_NOW with a priority score of 95/100."
    )

    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            captured_prompt["contents"] = kwargs["contents"]
            return SimpleNamespace(text=expected_summary)

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    result = GeminiExplainer.enhance(workflow_context)

    assert result["status"] == "completed"
    assert "FOLLOW_UP_NOW" in captured_prompt["contents"]
    assert "95" in captured_prompt["contents"]
    assert "LEAD-GEMINI-001" not in captured_prompt["contents"]
def test_gemini_preserves_request_data_recommendation(
    monkeypatch,
):
    lead = LeadRecord(
        lead_id="LEAD-MISSING-CONTACT",
        source="Website",
        created_at=datetime(2026, 11, 10, tzinfo=timezone.utc),
        stage="New",
        contact_available=False,
    )

    context = ContextBuilder.build(lead)

    context.final_recommendation = {
        "action": "REQUEST_DATA",
        "priority_score": 0,
        "triggered_rules": [],
        "reasons": ["Mandatory contact information is missing"],
    }

    ExplanationService.build(context)

    expected_summary = (
        "REQUEST_DATA with a priority score of 0/100 "
        "because mandatory contact information is missing."
    )

    class MockModels:
        @staticmethod
        def generate_content(**kwargs):
            return SimpleNamespace(text=expected_summary)

    class MockClient:
        def __init__(self, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr(
        "app.services.gemini_explainer.genai.Client",
        MockClient,
    )

    monkeypatch.setattr(
        "app.services.llm_config.LLMConfig.is_configured",
        classmethod(lambda cls: True),
    )

    result = GeminiExplainer.enhance(context)

    assert result["status"] == "completed"
    assert result["summary"] == expected_summary
    assert context.final_recommendation["action"] == "REQUEST_DATA"
    assert context.final_recommendation["priority_score"] == 0