import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAI client pointed at OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

OBSERVER_SYSTEM_PROMPT = """
You are a warehouse inspection observer. Your only job is to describe 
what you see in the image of a returned item. 

You must output ONLY a JSON object — no preamble, no explanation, 
no markdown. Just raw JSON.

Your observations must be purely factual. Do NOT grade the item. 
Do NOT recommend any action. Do NOT use evaluative words like 
'good', 'poor', 'acceptable', or 'damaged beyond repair'.

Describe only what is visually present.

Output this exact JSON structure:
{
    "product_type": "what the item appears to be",
    "brand": "brand name if visible, otherwise null",
    "color": "primary color(s)",
    "product_category": "electronics | apparel | general_retail",
    "packaging_present": true or false,
    "packaging_condition": "describe packaging state, or null if absent",
    "visible_physical_observations": [
        "observation 1",
        "observation 2"
    ],
    "components_observed": [
        "list any components, accessories, or parts visible"
    ],
    "text_visible": "any text, model numbers, or labels visible on item",
    "image_quality": "clear | partial | obscured"
}
"""

def encode_image(image_bytes: bytes) -> str:
    """
    Converts raw image bytes to base64 string.
    This is the format the vision API expects.
    """
    return base64.b64encode(image_bytes).decode("utf-8")


def run_observer(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """
    Agent 1 — Observer.
    Takes a raw image, returns structured factual observations.
    No grading. No judgment. Facts only.
    """
    try:
        # Encode image to base64
        image_b64 = encode_image(image_bytes)

        # Build the multimodal message — text + image together
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": OBSERVER_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Inspect this returned item and report your observations."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1
        )

        raw_response = response.choices[0].message.content

        # Strip markdown code fences if model adds them
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        # Parse into structured dict
        observer_output = json.loads(cleaned)

        return {
            "success": True,
            "observer_output": observer_output,
            "raw_response": raw_response
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Observer returned invalid JSON: {str(e)}",
            "raw_response": raw_response if 'raw_response' in locals() else ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": ""
        }