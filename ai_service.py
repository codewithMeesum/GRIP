"""Google GenAI integration with validated, transparent offline fallbacks."""
import json
import logging
import re
from typing import TypeVar
from pydantic import BaseModel
from prompts import (
    Analysis, Innovation, SYSTEM, ANALYSIS_PROMPT, INNOVATION_PROMPT, CATEGORIES,
)
from utils import prepare_image, utcnow

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Practical category-specific starter guidance. These are templates, not AI output.
GUIDANCE = {
    "Waste & litter": {
        "causes": ["Collection gaps may allow waste to accumulate.",
                   "Uncovered disposal points may let litter reach nearby drains or streams."],
        "actions": ["Document the extent from a safe, dry public location.",
                    "Ask the local waste service about collection and an approved disposal route.",
                    "Plan supervised removal of ordinary litter only; leave sharps and unknown waste to trained crews."],
        "name": "Community collection & recovery pilot",
        "solution": "Pair a small, scheduled collection route with covered sorting points and a confirmed downstream recycler. Prevent litter reaching water at its source.",
        "business": "Test a voluntary collection subscription with nearby shops. Recyclable sales can supplement fees only after a buyer confirms accepted materials and prices.",
        "metric": "Weigh safely collected litter by material and record its confirmed destination.",
        "benefit": "Could reduce escaped litter and increase material recovery; compare repeated site observations and weighed collections to a baseline.",
    },
    "Water pollution": {
        "causes": ["Runoff may be carrying sediment or waste into the water.",
                   "A drainage or wastewater connection may need investigation by qualified staff."],
        "actions": ["Record visible conditions from the bank without entering the water.",
                    "Request an assessment and suitable sampling by qualified water staff.",
                    "Record upstream activities without attributing blame; photos cannot establish water safety."],
        "name": "Stream observation & source-reduction pilot",
        "solution": "Create a fixed-point observation log and work with qualified water staff to investigate possible inputs before choosing a source-control intervention.",
        "business": "Explore a paid observation and reporting service for local associations; any laboratory testing must be performed by a qualified partner with transparent fees.",
        "metric": "Track repeat observations, investigated inputs and qualified test results when available.",
        "benefit": "Could help target pollution sources and track improvement; changes in water quality require appropriate measurements.",
    },
    "Air quality": {
        "causes": ["Open burning or local combustion may be contributing to the reported smoke.",
                   "Traffic or dry exposed surfaces may contribute to dust."],
        "actions": ["Observe from a safe distance; avoid smoke and do not confront operators.",
                    "Record time, duration and visible conditions without estimating pollutant levels.",
                    "Ask relevant local services to investigate and discuss alternatives to burning."],
        "name": "Clean-air observation & alternatives pilot",
        "solution": "Log recurring smoke observations and help willing local businesses test collection or process alternatives that avoid open burning.",
        "business": "Test a waste-collection coordination service with participating businesses, with transparent fees and a confirmed lawful disposal route.",
        "metric": "Record smoke-event frequency and participant use of the alternative service.",
        "benefit": "Could reduce local smoke events; measured exposure reductions require suitable monitoring.",
    },
    "Biodiversity": {
        "causes": ["Visitor pressure may be disturbing the habitat.",
                   "Habitat loss or inappropriate maintenance may be affecting vegetation."],
        "actions": ["Observe without approaching wildlife or sharing sensitive nest locations.",
                    "Ask a local conservation specialist to assess the affected habitat.",
                    "Agree on low-disturbance access and native habitat care with the land manager."],
        "name": "Habitat stewardship pilot",
        "solution": "Work with a local ecologist and land manager on a small protected observation area and an agreed native-habitat maintenance schedule.",
        "business": "Explore paid native-habitat maintenance for land managers; avoid wildlife capture, trade or unapproved planting.",
        "metric": "Track habitat condition and specialist-approved indicators at fixed observation points.",
        "benefit": "Could reduce disturbance and improve habitat condition; ecological benefits need seasonal observation.",
    },
    "Land & soil": {
        "causes": ["Exposed soil and runoff may be accelerating erosion.",
                   "Compaction or loss of vegetation may be reducing ground cover."],
        "actions": ["Photograph erosion from stable ground and avoid unstable slopes.",
                    "Ask a land or drainage specialist to assess runoff paths.",
                    "Agree on a small ground-cover intervention with the landowner before any earthworks."],
        "name": "Ground-cover & erosion observation pilot",
        "solution": "Map a small affected area and trial locally appropriate ground cover after a specialist checks stability and drainage.",
        "business": "Explore a small native-plant nursery and maintenance service for consenting landowners, validating demand before buying stock.",
        "metric": "Track ground-cover survival and repeat erosion observations after rainfall.",
        "benefit": "Could retain topsoil and improve ground cover; effectiveness depends on slope, soil and rainfall.",
    },
    "Other environmental issue": {
        "causes": ["A local service or maintenance gap may be involved.",
                   "The available observations may omit a contributing source."],
        "actions": ["Collect dated observations from a safe public location.",
                    "Ask a relevant environmental specialist to help define the problem.",
                    "Agree on a small, measurable intervention after the cause is better understood."],
        "name": "Local observation-to-action pilot",
        "solution": "Define one observable environmental problem with a local specialist, establish a baseline and test a small reversible intervention.",
        "business": "Explore a low-cost observation and maintenance service only after interviews establish who benefits and who is willing to pay.",
        "metric": "Track completed observations, agreed actions and a problem-specific baseline indicator.",
        "benefit": "Potential benefits depend on the confirmed issue; establish a measurable baseline before claiming improvement.",
    },
}


def local_analysis(report: dict) -> dict:
    category = report.get("category", CATEGORIES[-1])
    if category not in GUIDANCE:
        category = CATEGORIES[-1]
    guide = GUIDANCE[category]
    return Analysis(
        category=category,
        summary=f"Community observation at {report['location']}: {report['title']}. The description needs on-site review.",
        advisory_priority="Medium",
        possible_causes=guide["causes"],
        recommended_next_actions=guide["actions"],
        limitations="Local template based on the selected category and report text. No image interpretation or independent verification. Medium is a default review priority, not a measured risk level.",
    ).model_dump()


def local_innovation(report: dict, constraints: str = "") -> dict:
    guide = GUIDANCE.get(report.get("category"), GUIDANCE[CATEGORIES[-1]])
    return Innovation(
        solution_name=guide["name"],
        practical_solution=f"For {report['location']}: {guide['solution']}",
        implementation_approach=[
            "Identify a willing site coordinator, land manager and relevant qualified service provider.",
            guide["actions"][1],
            "Agree on permissions, safe roles, a collection or maintenance schedule, and a small resource budget before launch.",
        ],
        environmental_benefit=guide["benefit"],
        green_business_model=guide["business"],
        pilot_plan=[
            "Week 1 — inspect safely with the appropriate specialist, establish a baseline and interview potential participants.",
            "Week 2 — confirm permissions, partners, responsibilities and realistic costs; proceed only when essential dependencies are available.",
            "Weeks 3–4 — run a small trial, record results weekly and collect participant feedback.",
            "End of week 4 — compare with baseline and decide whether to adapt, stop or expand.",
        ],
        success_metrics=[guide["metric"],
                         "Track participation, total operating cost and willingness to continue paying or volunteering."],
        assumptions_and_risks=(
            "Local template, not a feasibility assessment. Partner availability, permissions and costs are unconfirmed. "
            + (f"User constraints to validate before launch: {constraints[:650]}" if constraints
               else "Validate the scope with the community before committing resources.")
        ),
    ).model_dump()


def parse_response(text: str, schema: type[T]) -> dict:
    """Accept plain JSON or a single fenced JSON block, then validate strictly."""
    if not isinstance(text, str) or len(text) > 60_000:
        raise ValueError("Missing or oversized response")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.I)
        text = re.sub(r"\s*```$", "", text, count=1)
    return schema.model_validate_json(text).model_dump()


def request_json(prompt: str, payload: dict, schema: type[T], key: str,
                 model: str, image: bytes | None = None) -> dict:
    # Import lazily: local demo guidance works even if the SDK import fails.
    from google import genai
    from google.genai import types

    contents = [prompt + "\nUntrusted report data:\n" + json.dumps(payload, ensure_ascii=False)]
    if image:
        normalized, _ = prepare_image(image)
        contents.append(types.Part.from_bytes(data=normalized, mime_type="image/jpeg"))
    options = types.HttpOptions(timeout=25_000, retry_options=types.HttpRetryOptions(attempts=1))
    with genai.Client(api_key=key, http_options=options) as client:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM,
                response_mime_type="application/json",
                response_json_schema=schema.model_json_schema(),
                temperature=0.25,
                max_output_tokens=4096,
            ),
        )
        return parse_response(response.text, schema)


def generate(report: dict, kind: str = "analysis", *, key: str = "",
             model: str = "gemini-2.5-flash", force_demo: bool = False,
             image: bytes | None = None, constraints: str = "") -> dict:
    """Return a stored envelope. Exceptions and credentials never reach the UI."""
    if kind not in {"analysis", "innovation"}:
        raise ValueError("Unsupported generation type")
    payload = {field: report[field] for field in ("title", "description", "category", "location")}
    if len(constraints) > 1000:
        raise ValueError("Constraints must be at most 1000 characters.")
    fallback = local_analysis(report) if kind == "analysis" else local_innovation(report, constraints)
    schema = Analysis if kind == "analysis" else Innovation
    prompt = ANALYSIS_PROMPT if kind == "analysis" else INNOVATION_PROMPT
    if kind == "innovation":
        payload["constraints"] = constraints
    result = {
        "source": "Local guidance", "data": fallback, "created_at": utcnow(),
        "notice": "Gemini is not configured. Category-based local guidance is shown.",
        "model": None,
    }
    if force_demo:
        result["notice"] = "Demo mode is enabled. Category-based local guidance is shown."
    elif key:
        try:
            result.update(data=request_json(prompt, payload, schema, key, model, image),
                          source="Gemini", model=model,
                          notice="AI-generated advice. Review locally; not official verification.")
        except Exception as exc:
            # Deliberately exclude exception messages: SDK errors may contain request details.
            logger.warning("Gemini unavailable (%s); using local guidance", type(exc).__name__)
            result["notice"] = "Gemini could not complete this request. Local guidance is shown; you can retry later."
    return result
