import json

"""
Stores the prompt templates and helper functions for building prompts for the Gemini API.
"""

# Prompt template for analyzing a LinkedIn profile
PROFILE_PROMPT_TEMPLATE = """
Summarize the following LinkedIn profile into JSON with keys strengths[], tone, niche, voice. Be concise. Text: <<<{}>>>
"""

# Prompt template for analyzing a trend or news article
TRENDS_PROMPT_TEMPLATE = """
From the text below, extract 3-5 concise, non-generic insights as a JSON array 'insights'. Keep each <= 18 words. Text: <<<{}>>>
"""

# Prompt template for image analysis
IMAGE_PROMPT_TEMPLATE = """
Analyze the image and provide a concise description and a list of relevant tags in JSON format with keys 'description' and 'tags[]'.
"""

# Prompt template for generating a LinkedIn post
POST_PROMPT_TEMPLATE = """
Using the provided information, write a LinkedIn post (<= 200 words) in a professional, friendly tone. End with a short CTA. Return JSON with keys post, hashtags[5-8 relevant tags].

Profile Summary: <<<{}>>>
Trend Insights: <<<{}>>>
Image Analysis: <<<{}>>>
"""

def build_profile_prompt(text: str) -> str:
    """Builds the prompt for profile analysis."""
    return PROFILE_PROMPT_TEMPLATE.format(text)

def build_trends_prompt(text: str) -> str:
    """Builds the prompt for trend analysis."""
    return TRENDS_PROMPT_TEMPLATE.format(text)

def build_image_prompt() -> str:
    """
    Builds the prompt for image analysis. No text input needed as the image is the primary input.
    """
    return IMAGE_PROMPT_TEMPLATE

def build_post_prompt(profile_summary: dict, trend_insights: dict, image_analysis: dict = None) -> str:
    """
    Builds the prompt for post generation, optionally including image analysis.
    """
    profile_summary_json = json.dumps(profile_summary)
    trend_insights_json = json.dumps(trend_insights)
    image_analysis_json = json.dumps(image_analysis) if image_analysis else "No image analysis provided."

    return POST_PROMPT_TEMPLATE.format(profile_summary_json, trend_insights_json, image_analysis_json)