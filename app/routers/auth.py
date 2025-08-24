from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from app.config import settings
from typing import Optional
import requests

# Import our project modules
from app import linkedin_client
from app.ai import gemini_client, prompts
from app.db import database

router = APIRouter()

# LinkedIn OAuth2 configuration
LINKEDIN_AUTHORIZATION_BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# Scopes requested from LinkedIn - r_liteprofile is needed for the /v2/me endpoint
LINKEDIN_SCOPES = ["openid", "profile", "email", "w_member_social", "r_liteprofile"]

def analyze_and_store_profile(access_token: str):
    """
    Background task to fetch, analyze, and store a user's LinkedIn profile.
    """
    try:
        print("Starting background profile analysis...")
        # 1. Fetch detailed profile from LinkedIn
        profile_data = linkedin_client.get_user_profile(access_token)
        user_id = profile_data.get("id")
        if not user_id:
            print("Error: Could not get user ID from LinkedIn profile.")
            return

        # 2. Create a simple text summary for the AI
        # Combining first and last names
        first_name = profile_data.get('localizedFirstName', '')
        last_name = profile_data.get('localizedLastName', '')
        full_name = f"{first_name} {last_name}".strip()
        headline = profile_data.get("headline", "")
        profile_text = f"Name: {full_name}\nHeadline: {headline}"

        # 3. Build the prompt and call the AI for analysis
        prompt = prompts.build_profile_prompt(profile_text)
        analysis_result = gemini_client.call_gemini_json([prompt])

        if not analysis_result or "error" in analysis_result:
            print(f"Error analyzing profile with Gemini: {analysis_result.get('error')}")
            return

        # 4. Save the analysis to the database
        database.upsert_user_profile(user_id, analysis_result)
        print(f"Successfully analyzed and stored profile for user {user_id}")

    except Exception as e:
        print(f"An error occurred during background profile analysis: {e}")

@router.get("/auth/login")
def linkedin_login(request: Request):
    """
    Initiates the LinkedIn OAuth2 login flow.
    """
    redirect_uri = request.url_for("linkedin_callback")
    linkedin = OAuth2Session(
        settings.LINKEDIN_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope=LINKEDIN_SCOPES
    )
    authorization_url, state = linkedin.authorization_url(LINKEDIN_AUTHORIZATION_BASE_URL)

    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)

@router.get("/auth/linkedin/callback", name="linkedin_callback")
def linkedin_callback(request: Request, background_tasks: BackgroundTasks, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """
    Handles the callback from LinkedIn, gets the token, and triggers background profile analysis.
    """
    if error:
        print(f"LinkedIn OAuth error: {error}")
        return RedirectResponse("/")

    if state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing.")

    redirect_uri = request.url_for("linkedin_callback")

    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }

    try:
        response = requests.post(LINKEDIN_TOKEN_URL, data=token_data)
        response.raise_for_status()
        token = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token from LinkedIn: {e}")
        if response is not None: print(f"LinkedIn response: {response.text}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {e}")

    request.session["linkedin_token"] = token
    access_token = token.get("access_token")

    if access_token:
        # Get user profile to store user_id in session
        try:
            profile_data = linkedin_client.get_user_profile(access_token)
            user_id = profile_data.get("id")
            if user_id:
                request.session["user_id"] = user_id
                # --- New Feature: Trigger Profile Analysis ---
                # Add the analysis as a background task so it doesn't block the redirect
                background_tasks.add_task(analyze_and_store_profile, access_token)
                # --- End New Feature ---
        except Exception as e:
            print(f"Error getting user profile: {e}")

    return RedirectResponse("/")
