import os
import re
import json
import google.generativeai as genai # Will be google.genai after pip install
from app.config import settings

def init_gemini():
    """
    Initializes the Gemini client by configuring the generative AI model
    using the API key from settings.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=settings.GEMINI_API_KEY)

def call_gemini_json(prompt_parts: list) -> dict:
    """
    Calls the Gemini API with a given list of prompt parts (text and/or image data)
    and expects a JSON response.

    Args:
        prompt_parts: A list containing text strings and/or dictionaries
                      for image data (e.g., {"mime_type": "image/jpeg", "data": image_bytes}).

    Returns:
        A dictionary parsed from the model's JSON response.
        Returns an error dictionary if the call fails or parsing is unsuccessful.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3
            )
        )
        
        text_response = response.text

        try:
            # Try direct JSON parsing first
            return json.loads(text_response)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code blocks
            json_match = re.search(r"""```json\n({.*?})\n```""", text_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                # If no JSON found, return raw text in an error format
                return {"error": "AI response not valid JSON", "raw_response": text_response}

    except Exception as e:
        print(f"Error calling Gemini or parsing JSON: {e}")
        return {"error": str(e)}

# --- Smoke Test ---
# To run this test:
# 1. Make sure you have a .env file with your GEMINI_API_KEY.
# 2. Run this file directly: python -m app.ai.gemini_client
if __name__ == '__main__':
    print("Running Gemini client smoke test...")
    try:
        init_gemini()
        
        # Test Case 1: A simple prompt that should return JSON
        test_prompt_parts = ['Return a JSON object with a key "greeting" and value "hello".']
        print(f"\nTesting with prompt: '{test_prompt_parts}'")
        result = call_gemini_json(test_prompt_parts)
        
        print(f"Result: {result}")
        assert "greeting" in result and result["greeting"] == "hello"
        print("Smoke test PASSED.")

    except Exception as e:
        print(f"Smoke test FAILED: {e}")
