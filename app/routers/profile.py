from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from app.ai import gemini_client, prompts
from app.state import latest_analysis

router = APIRouter()

@router.post("/profile/analyze")
def analyze_profile(text: str = Form(...)):
    """
    Analyzes the provided LinkedIn profile text.
    Stores the result in the in-memory state and redirects to the main page.
    """
    # Build the prompt and call the AI
    prompt = prompts.build_profile_prompt(text)
    summary = gemini_client.call_gemini_json(prompt)

    # Store the result
    latest_analysis["profile_summary"] = summary

    # Redirect back to the home page to see the results
    return RedirectResponse("/", status_code=303)