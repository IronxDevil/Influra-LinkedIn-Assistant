from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from app.ai import gemini_client, prompts
from app.state import latest_analysis
from typing import List

router = APIRouter()

@router.post("/image/analyze")
async def analyze_image(request: Request, images: List[UploadFile] = File(...)):
    """
    Analyzes uploaded images using Gemini Vision.
    Stores the result in the in-memory state and redirects to the main page.
    """
    try:
        all_image_data = []
        all_image_mime_types = []
        prompt_parts = []

        for image in images:
            image_data = await image.read()
            image_mime_type = image.content_type
            all_image_data.append(image_data)
            all_image_mime_types.append(image_mime_type)
            prompt_parts.append({"mime_type": image_mime_type, "data": image_data})
        
        # Add the text prompt for image analysis
        prompt_parts.append({"text": prompts.IMAGE_PROMPT_TEMPLATE})
        
        analysis_result = gemini_client.call_gemini_json(prompt_parts)

        # Store the result and image data
        latest_analysis["image_analysis"] = analysis_result
        latest_analysis["image_data"] = all_image_data
        latest_analysis["image_mime_types"] = all_image_mime_types

    except Exception as e:
        print(f"Error analyzing image: {e}")
        latest_analysis["image_analysis"] = {"error": str(e)}
        latest_analysis["image_data"] = []
        latest_analysis["image_mime_types"] = []

    return RedirectResponse("/", status_code=303)
