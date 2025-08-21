from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from app.config import settings
from typing import Optional
import requests # Import requests

router = APIRouter()

# LinkedIn OAuth2 configuration
LINKEDIN_AUTHORIZATION_BASE_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/userinfo"

# Scopes requested from LinkedIn
LINKEDIN_SCOPES = ["openid", "profile", "email", "w_member_social"]

@router.get("/auth/login")
def linkedin_login(request: Request):
    """
    Initiates the LinkedIn OAuth2 login flow.
    """
    redirect_uri = "http://localhost:8000/auth/linkedin/callback"
    linkedin = OAuth2Session(
        settings.LINKEDIN_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope=LINKEDIN_SCOPES
    )
    authorization_url, state = linkedin.authorization_url(LINKEDIN_AUTHORIZATION_BASE_URL)

    request.session["oauth_state"] = state
    return RedirectResponse(authorization_url)

@router.get("/auth/linkedin/callback", name="linkedin_callback")
def linkedin_callback(request: Request, code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
    """
    Handles the callback from LinkedIn after user authorization.
    Exchanges the authorization code for an access token and stores it in the session.
    """
    if error:
        print(f"LinkedIn OAuth error: {error}")
        return RedirectResponse("/")

    if state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid state parameter.")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing.")

    redirect_uri = "http://localhost:8000/auth/linkedin/callback"

    # Manually construct the token request to ensure client_secret is sent correctly
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }

    try:
        response = requests.post(LINKEDIN_TOKEN_URL, data=token_data)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        token = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token from LinkedIn: {e}")
        if response is not None:
            print(f"LinkedIn response: {response.text}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"An unexpected error occurred: {e}")

    request.session["linkedin_token"] = token

    return RedirectResponse("/")