# A simple in-memory store for the application state.

# This will hold the latest analysis results to be used in post generation.
# In a production app, this would be replaced by a more robust session management
# system like Redis, a database cache, or client-side storage.

latest_analysis = {
    "profile_summary": None,
    "trend_insights": None,
    "image_analysis": None, # Added for image analysis results
    "image_data": [],      # Changed to list for multiple images
    "image_mime_types": []  # Changed to list for multiple images
}