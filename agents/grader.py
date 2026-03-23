import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

GRADER_SYSTEM_PROMPT = """
You are an adversarial quality grader for a 3rd party reverse logistics 
operation. You receive structured observations from an independent 
inspector and apply grading standards to determine disposition.

Your role is deliberately adversarial — you must challenge the 
observations and stress-test them before reaching a grade. Ask yourself:
- Is anything ambiguous in the observations?
- What is the worst reasonable interpretation of what was observed?
- What would a client dispute if they saw this grade?

Grading standards:
- Grade A: Item appears to be in original or near-original condition. 
  Packaging intact or minor cosmetic issues only. Suitable for resale 
  as new or open-box.
- Grade B: Item shows visible wear, minor damage, or incomplete 
  packaging. Functional condition likely. Suitable for refurbishment 
  or secondary market resale.
- Grade C: Item shows significant damage, missing components, or 
  heavily compromised packaging. Parts recovery or liquidation only.
- Scrap: Item appears non-functional, heavily damaged, or has no 
  recoverable value. Recycle or dispose.

Disposition channels:
- Grade A → Restock as new / Open-box resale
- Grade B → Refurbishment pipeline / Secondary market
- Grade C → Liquidation / Parts recovery
- Scrap → Recycling / Disposal

You must output ONLY a JSON object — no preamble, no explanation,
no markdown. Just raw JSON.

Output this exact JSON structure:
{
    "grade": "A | B | C | Scrap",
    "confidence": "high | medium | low",
    "disposition": "recommended channel",
    "adversarial_challenges": [
        "challenge 1 you considered",
        "challenge 2 you considered"
    ],
    "reasoning": "your final reasoning after challenges",
    "flags": [
        "any concerns that should be reviewed by a human supervisor"
    ],
    "estimated_value_recovery": "high | medium | low | none"
}
"""

def run_grader(observer_output: dict) -> dict:
    """
    Agent 2 — Grader.
    Takes Observer's structured facts, applies adversarial grading.
    Never sees the raw image — works only from structured observations.
    """
    try:
        # Format observer output as clean input for grader
        observer_summary = json.dumps(observer_output, indent=2)

        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": GRADER_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""
Based on the following inspection observations, apply your grading 
standards and determine the appropriate grade and disposition.

INSPECTION OBSERVATIONS:
{observer_summary}

Apply adversarial review before reaching your final grade.
"""
                }
            ],
            temperature=0.2
        )

        raw_response = response.choices[0].message.content

        # Strip markdown fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        grader_output = json.loads(cleaned)

        return {
            "success": True,
            "grade": grader_output.get("grade"),
            "confidence": grader_output.get("confidence"),
            "disposition": grader_output.get("disposition"),
            "adversarial_challenges": grader_output.get("adversarial_challenges", []),
            "reasoning": grader_output.get("reasoning"),
            "flags": grader_output.get("flags", []),
            "estimated_value_recovery": grader_output.get("estimated_value_recovery"),
            "raw_response": raw_response,
            "full_output": grader_output
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Grader returned invalid JSON: {str(e)}",
            "raw_response": raw_response if 'raw_response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": ""
        }