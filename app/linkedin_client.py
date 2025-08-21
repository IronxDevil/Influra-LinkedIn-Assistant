import requests
import json

# LinkedIn API Endpoints
LINKEDIN_UGC_POST_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_PERSON_URN_URL = "https://api.linkedin.com/v2/userinfo" # Changed to userinfo
LINKEDIN_ASSET_UPLOAD_REGISTER_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"

def get_person_urn(access_token: str) -> str:
    """
    Fetches the authenticated user's Person URN (Unique Resource Name).
    This is required to create a post on LinkedIn.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        # "X-Restli-Protocol-Version": "2.0.0" # Not typically needed for userinfo
    }
    try:
        response = requests.get(LINKEDIN_PERSON_URN_URL, headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        # For userinfo, the unique identifier is 'sub'
        return f"urn:li:person:{data['sub']}"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Person URN: {e}")
        if response is not None:
            print(f"LinkedIn response: {response.text}")
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
        if register_response is not None:
            print(f"LinkedIn Register response: {register_response.text}")
        if upload_response is not None:
            print(f"LinkedIn Upload response: {upload_response.text}")
        raise

def post_linkedin_update(access_token: str, post_content: str, image_urns: list = None) -> dict:
    """
    Posts an update to LinkedIn on behalf of the authenticated user.

    Args:
        access_token: The user's LinkedIn access token.
        post_content: The text content of the post.
        image_urns: Optional. A list of URNs of uploaded image assets to include in the post.

    Returns:
        A dictionary containing the response from LinkedIn, or an error.
    """
    person_urn = get_person_urn(access_token)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    # Base payload for a text post
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

    # Add image content if image_urns are provided
    if image_urns:
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = []
        for urn in image_urns:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"].append(
                {
                    "status": "READY",
                    "media": urn,
                    "mediaUrn": urn,
                    "categories": [
                        "IMAGE"
                    ]
                }
            )
        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"

    try:
        response = requests.post(LINKEDIN_UGC_POST_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error posting to LinkedIn: {e}")
        if response is not None:
            print(f"LinkedIn response: {response.text}")
        return {"error": str(e), "linkedin_response": response.text if response is not None else ""}