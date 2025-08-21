from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.ai import gemini_client, prompts
from app.state import latest_analysis

router = APIRouter()

@router.post("/trends/analyze")
def analyze_trends(text: str = Form(...)):
    """
    Analyzes the provided trend or news text.
    Stores the result in the in-memory state and redirects to the main page.
    """
    prompt = prompts.build_trends_prompt(text)
    insights = gemini_client.call_gemini_json(prompt)

    latest_analysis["trend_insights"] = insights

    return RedirectResponse("/", status_code=303)