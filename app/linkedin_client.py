import requests
import json

# LinkedIn API Endpoints
LINKEDIN_UGC_POST_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_USER_INFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/me" # For detailed profile
LINKEDIN_ASSET_UPLOAD_REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"

def get_person_urn(access_token: str) -> str:
    """
    Fetches the authenticated user's Person URN (Unique Resource Name) from the userinfo endpoint.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(LINKEDIN_USER_INFO_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        return f"urn:li:person:{data['sub']}"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Person URN: {e}")
        if response is not None: print(f"LinkedIn response: {response.text}")
        raise

def get_user_profile(access_token: str) -> dict:
    """
    Fetches the authenticated user's detailed profile from the /v2/me endpoint.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    # Define the specific fields you want to retrieve.
    # This projection requests the user's ID, name, headline, and profile picture.
    params = {"projection": "(id,localizedFirstName,localizedLastName,headline)"}
    try:
        response = requests.get(LINKEDIN_PROFILE_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user profile: {e}")
        if response is not None: print(f"LinkedIn response: {response.text}")
        raise

def upload_image_to_linkedin(access_token: str, image_data: bytes, mime_type: str) -> str:
    """
    Uploads an image to LinkedIn's asset API and returns the asset URN.
    """
    person_urn = get_person_urn(access_token)

    # Step 1: Register the upload
    register_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    register_payload = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": person_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }

    try:
        register_response = requests.post(
            LINKEDIN_ASSET_UPLOAD_REGISTER_URL,
            headers=register_headers,
            data=json.dumps(register_payload)
        )
        register_response.raise_for_status()
        register_data = register_response.json()
        
        upload_url = register_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_data['value']['asset']

        # Step 2: Upload the image binary data
        upload_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": mime_type # Use the actual image MIME type
        }
        upload_response = requests.put(upload_url, headers=upload_headers, data=image_data)
        upload_response.raise_for_status()

        return asset_urn

    except requests.exceptions.RequestException as e:
        print(f"Error uploading image to LinkedIn: {e}")
        if 'register_response' in locals() and register_response is not None:
            print(f"LinkedIn Register response: {register_response.text}")
        if 'upload_response' in locals() and upload_response is not None:
            print(f"LinkedIn Upload response: {upload_response.text}")
        raise

def post_linkedin_update(access_token: str, post_content: str, image_urns: list = None) -> dict:
    """
    Posts an update to LinkedIn on behalf of the authenticated user.
    """
    person_urn = get_person_urn(access_token)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    if image_urns:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = []
        for urn in image_urns:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"].append(
                {
                    "status": "READY",
                    "media": urn
                }
            )
        # Correctly set shareMediaCategory based on content
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"

    try:
        response = requests.post(LINKEDIN_UGC_POST_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to LinkedIn: {e}")
        if response is not None:
            print(f"LinkedIn response: {response.text}")
        return {"error": str(e), "linkedin_response": response.text if response is not None else ""}
