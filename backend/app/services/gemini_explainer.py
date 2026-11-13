
import json

from google import genai
from google.genai import types

from app.models.workflow import WorkflowContext
from app.services.llm_config import LLMConfig


class GeminiExplainer:

    MAX_SUMMARY_LENGTH = 500

    @staticmethod
    def enhance(context: WorkflowContext) -> dict:
        explanation = context.explanation or {}
        recommendation = context.final_recommendation or {}

        fallback_summary = explanation.get("summary", "")

        fallback_result = {
            "summary": fallback_summary,
            "status": "fallback",
            "provider": "gemini",
            "model": LLMConfig.MODEL,
            "reason": "provider_unavailable",
        }

        if not LLMConfig.is_configured():
            fallback_result["reason"] = "not_configured"
            return fallback_result

        action = recommendation.get("action", "NOT_AVAILABLE")
        score = recommendation.get("priority_score", 0)

        # Do not send the lead identifier to the external LLM.
        evidence = {
            "recommendation": action,
            "priority_score": score,
            "score_breakdown": explanation.get(
                "score_breakdown", {}
            ),
            "triggered_rules": explanation.get(
                "triggered_rules", []
            ),
            "reasons": explanation.get("reasons", []),
            "executed_agents": explanation.get(
                "executed_agents", []
            ),
        }

        prompt = f"""
You are an explanation assistant for a deterministic sales
lead prioritization system.

Rewrite the existing decision explanation into a clear,
professional summary of one or two sentences.

Use ONLY the supplied structured evidence.

Mandatory requirements:
- Preserve the exact recommendation action.
- Preserve the exact priority score out of 100.
- Do not invent facts or add unsupported reasons.
- Do not change, reinterpret, or question the decision.
- Do not make predictions or promises.
- Do not make claims about health, legal compliance,
  or customer behavior beyond the supplied evidence.
- Do not recommend contacting a customer autonomously.
- Return only the rewritten summary, without headings.

Structured evidence:
{json.dumps(evidence, ensure_ascii=False)}
"""

        try:
            client = genai.Client(
                api_key=LLMConfig.API_KEY,
                http_options=types.HttpOptions(
                    timeout=int(LLMConfig.TIMEOUT * 1000)
                ),
            )

            response = client.models.generate_content(
                model=LLMConfig.MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=120,
                ),
            )

            summary = (response.text or "").strip()

            if not GeminiExplainer._is_valid_summary(
                summary,
                action,
                score,
            ):
                fallback_result["reason"] = "invalid_response"
                return fallback_result

            return {
                "summary": summary,
                "status": "completed",
                "provider": "gemini",
                "model": LLMConfig.MODEL,
                "reason": "none",
            }

        except Exception as exc:
            fallback_result["reason"] = (
                "timeout"
                if "timeout" in type(exc).__name__.lower()
                else "provider_error"
            )
            return fallback_result

    @staticmethod
    def _is_valid_summary(
        summary: str,
        action: str,
        score,
    ) -> bool:
        if not summary:
            return False

        if len(summary) > GeminiExplainer.MAX_SUMMARY_LENGTH:
            return False

        if "\n" in summary or "\r" in summary:
            return False

        required_values = [
            action,
            str(score),
        ]

        normalized_summary = summary.casefold()

        return all(
            value.casefold() in normalized_summary
            for value in required_values
        )