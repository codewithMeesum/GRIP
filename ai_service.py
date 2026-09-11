import json
import os
from typing import Optional

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# =========================================================
# API KEY
# =========================================================
def _get_key():
    key = os.getenv("GEMINI_API_KEY")

    if key:
        return key

    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _client():
    key = _get_key()

    if not key or genai is None:
        return None

    try:
        return genai.Client(api_key=key)
    except Exception:
        return None


# =========================================================
# JSON PARSER
# =========================================================
def _parse_json(text: str):
    text = (text or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end < start:
        raise ValueError(
            "Model returned no JSON object."
        )

    return json.loads(
        text[start:end + 1]
    )


def _safe_list(value, fallback):
    if isinstance(value, list):
        cleaned = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        if cleaned:
            return cleaned

    return fallback


# =========================================================
# FALLBACK ANALYSIS
# =========================================================
def _fallback_analysis(
    title,
    category,
    location,
    description,
):
    return {
        "category": category,
        "summary": (
            f"{title}: "
            f"{description[:220]}"
        ),
        "priority": "Medium",
        "possible_causes": [
            "Needs local verification",
            "Insufficient contextual evidence",
        ],
        "next_actions": [
            "Verify the report and location",
            "Document additional evidence",
            "Refer to an appropriate local organization",
        ],
    }


# =========================================================
# ENVIRONMENTAL REPORT ANALYSIS
# =========================================================
def analyze_environmental_report(
    title,
    category,
    location,
    description,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
):
    client = _client()

    if not client:
        return _fallback_analysis(
            title,
            category,
            location,
            description,
        )

    # IMPORTANT:
    # This is NOT an f-string.
    # Therefore the JSON braces below are treated
    # literally and cannot trigger the previous error.
    prompt = f"""
You are GRIP, an environmental reporting assistant.

Analyze the submitted report conservatively.

AI output is advisory and must never be presented
as official verification.

Return ONLY valid JSON with exactly these keys:

{{
  "category": "Water|Waste|Air|Climate|Biodiversity|Other",
  "summary": "one concise sentence",
  "priority": "Low|Medium|High",
  "possible_causes": ["cause 1", "cause 2"],
  "next_actions": ["action 1", "action 2", "action 3"]
}}

Rules:
- Use only the submitted evidence and description.
- Priority is advisory triage, not a scientific or legal risk assessment.
- Never claim the report is true, officially verified, or legally established.
- Prefer practical verification and reporting steps.
- Keep the response concise.

Title: {title}
User-selected category: {category}
Location: {location}
Description: {description}
"""

    contents = [prompt]

    if (
        image_bytes
        and mime_type
        and types
    ):
        try:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            )
        except Exception:
            pass

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
        )

        parsed = _parse_json(
            response.text
        )

        allowed_categories = {
            "Water",
            "Waste",
            "Air",
            "Climate",
            "Biodiversity",
            "Other",
        }

        allowed_priorities = {
            "Low",
            "Medium",
            "High",
        }

        result = {
            "category": (
                parsed.get("category")
                if parsed.get("category")
                in allowed_categories
                else category
            ),
            "summary": str(
                parsed.get(
                    "summary",
                    "AI analysis unavailable.",
                )
            ).strip(),
            "priority": (
                parsed.get("priority")
                if parsed.get("priority")
                in allowed_priorities
                else "Medium"
            ),
            "possible_causes": _safe_list(
                parsed.get("possible_causes"),
                ["Needs local verification"],
            ),
            "next_actions": _safe_list(
                parsed.get("next_actions"),
                [
                    "Verify the report and location",
                    "Document additional evidence",
                ],
            ),
        }

        return result

    except Exception:
        return _fallback_analysis(
            title,
            category,
            location,
            description,
        )


# =========================================================
# FALLBACK INNOVATION
# =========================================================
def _fallback_innovation(report):
    return {
        "problem": report["description"],
        "solution": (
            "Design a small local service or product "
            "that reduces the identified environmental "
            "harm and can be piloted in one location."
        ),
        "implementation": (
            "Start with one site, define the service, "
            "test with a small user group, measure results, "
            "and improve before scaling."
        ),
        "environmental_benefit": (
            "Potential reduction in local environmental harm, "
            "subject to measurement and validation."
        ),
        "business_model": (
            "Offer the validated service to schools, "
            "businesses, community groups, tourism operators, "
            "or organizations through a subscription or service fee."
        ),
        "pilot": (
            "Run a 2–4 week pilot at one site and compare "
            "simple before/after indicators."
        ),
    }


# =========================================================
# GREEN INNOVATION
# =========================================================
def generate_green_innovation(report):
    client = _client()

    if not client:
        return _fallback_innovation(report)

    prompt = f"""
You are GRIP's Green Innovation Lab.

Turn the environmental problem below into a realistic,
Pakistan-relevant green solution and possible business opportunity.

Return ONLY valid JSON with exactly these keys:

{{
  "problem": "...",
  "solution": "...",
  "implementation": "...",
  "environmental_benefit": "...",
  "business_model": "...",
  "pilot": "..."
}}

Rules:
- Avoid unrealistic claims.
- Keep the idea feasible for a student hackathon team.
- Suggest a practical pilot.
- Clearly distinguish a possible business opportunity from a guaranteed business.
- Do not claim that the solution is already validated.

Problem title: {report["title"]}
Category: {report["category"]}
Location: {report["location"]}
Description: {report["description"]}
"""

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
        )

        parsed = _parse_json(
            response.text
        )

        required_keys = [
            "problem",
            "solution",
            "implementation",
            "environmental_benefit",
            "business_model",
            "pilot",
        ]

        if not all(
            key in parsed
            for key in required_keys
        ):
            raise ValueError(
                "Missing innovation fields."
            )

        return {
            key: str(
                parsed.get(key, "")
            ).strip()
            for key in required_keys
        }

    except Exception:
        return _fallback_innovation(report)
