# Influra MVP

A minimal working app to generate LinkedIn content from profiles and trends.

## Setup

### 1. Environment & Dependencies

Create and activate a Python virtual environment:

```bash
# For macOS/Linux
python3 -m venv .venv && source .venv/bin/activate

# For Windows
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Gemini API Key

This project uses the Google Gemini API. You will need to obtain an API key to run the application.

1.  **Get an API key:** Visit [Google AI Studio](https://aistudio.google.com/app/apikey) to create your API key.
2.  **Create a `.env` file:** In the project root directory, create a new file named `.env` (you can copy `.env.example`).
3.  **Add the key to `.env`:** Add your API key to the `.env` file as follows:

    ```
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## Running the Application

Once the setup is complete, run the FastAPI server using the robust command:

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## How to Use

The application provides a simple, one-page dashboard with a 4-step workflow:

1.  **Analyze Profile:** Paste the text of a LinkedIn profile into the first text area and click "Analyze". The page will reload and display an AI-generated summary of the profile's tone, niche, and strengths.
2.  **Analyze Trend:** Paste the text of a news article or a trend summary into the second text area and click "Distill Insights". The page will reload and show 3-5 key insights from the text.
3.  **Generate & Save Post:** Once both a profile and a trend have been analyzed, click the "Generate Post" button. The page will reload with a generated LinkedIn post in a text area. You can then click "Save Draft" to save it to the database.
4.  **Manage Drafts:** All saved drafts appear in a table at the bottom of the page. You can mark them as "posted" or export all drafts to Markdown or CSV files using the export buttons.

## API Testing

For this MVP, the primary endpoints are designed to be used with standard HTML form submissions, which then redirect back to the main page. There is no complex JSON API intended for external use.

The only pure JSON endpoint is the health check, which can be tested from your terminal:

```bash
curl http://127.0.0.1:8000/health
```

Expected output:
```json
{"status":"ok"}
```

## Screenshots

*(placeholder for you to add screenshots of the application)*