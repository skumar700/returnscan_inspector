import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def log_inspection(
    item_description: str,
    product_category: str,
    observer_output: dict,
    grade: str,
    disposition: str,
    grader_reasoning: str,
    confidence_level: str,
    raw_observer_response: str,
    raw_grader_response: str
) -> dict:
    """
    Logs a complete inspection record to Supabase.
    Stores both structured data (for querying) and
    raw responses (for audit trail).
    """
    try:
        record = {
            "item_description": item_description,
            "product_category": product_category,
            "observer_output": observer_output,
            "grade": grade,
            "disposition": disposition,
            "grader_reasoning": grader_reasoning,
            "confidence_level": confidence_level,
            "raw_observer_response": raw_observer_response,
            "raw_grader_response": raw_grader_response
        }

        result = supabase.table("inspections").insert(record).execute()
        return {"success": True, "data": result.data}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_recent_inspections(limit: int = 10) -> list:
    """
    Retrieves the most recent inspections.
    Used by the UI to show inspection history.
    """
    try:
        result = (
            supabase.table("inspections")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        return []