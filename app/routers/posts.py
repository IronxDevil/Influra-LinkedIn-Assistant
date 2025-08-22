from fastapi import APIRouter, Form, Response, Request, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from app.ai import gemini_client, prompts
from app.state import latest_analysis
from app.db import database
from app import linkedin_client # Import the new linkedin_client
import io
import csv
from typing import List

router = APIRouter()

@router.post("/post/generate")
def generate_post(manual_context: str = Form(None)):
    """
    Generates a LinkedIn post using the stored profile, trend analysis, and optional manual context.
    Stores the generated post in the in-memory state.
    """
    profile_summary = latest_analysis.get("profile_summary")
    trend_insights = latest_analysis.get("trend_insights")
    image_analysis = latest_analysis.get("image_analysis") # Get image analysis

    # Ensure we have at least profile and trend for a basic post
    if not profile_summary or not trend_insights:
        latest_analysis["generated_post"] = {"error": "Please analyze a profile and trends before generating a post.", "raw_response": ""}
        return RedirectResponse("/", status_code=303)

    # Pass image_analysis and manual_context to the prompt builder
    prompt_text = prompts.build_post_prompt(profile_summary, trend_insights, image_analysis, manual_context)
    
    # Call Gemini
    generated_post = gemini_client.call_gemini_json([prompt_text]) # Pass as list for multimodal compatibility

    latest_analysis["generated_post"] = generated_post

    return RedirectResponse("/", status_code=303)

@router.post("/posts/save")
def save_post():
    """
    Saves the latest generated post to the database.
    """
    post_data = latest_analysis.get("generated_post")
    if post_data and 'post' in post_data and 'hashtags' in post_data:
        content = post_data['post']
        hashtags_str = ", ".join(post_data['hashtags'])
        database.insert_post(content, hashtags_str)
        latest_analysis["generated_post"] = None

    return RedirectResponse("/", status_code=303)

@router.post("/posts/delete")
def delete_posts(post_ids: List[int] = Form(...)):
    """
    Deletes one or more posts from the database.
    """
    if not post_ids:
        # Redirect back if no IDs were provided, though the form shouldn't allow this.
        return RedirectResponse("/", status_code=303)
    
    # The Form(...) will automatically handle parsing the list of integers.
    # In the HTML, each checkbox will have the name "post_ids" and the value of the post ID.
    database.delete_posts(post_ids)
    
    return RedirectResponse("/", status_code=303)

@router.post("/posts/{post_id}/mark_posted")
def mark_post_as_posted(post_id: int):
    """
    Marks a specific post as 'posted' in the database.
    This is the simulated 'mark as posted' functionality.
    """
    database.mark_posted(post_id)
    return RedirectResponse("/", status_code=303)

@router.post("/posts/{post_id}/share")
def share_post_on_linkedin(request: Request, post_id: int):
    """
    Shares a saved post to LinkedIn using the authenticated user's token.
    """
    linkedin_token = request.session.get("linkedin_token")
    if not linkedin_token:
        raise HTTPException(status_code=401, detail="Not authenticated with LinkedIn. Please log in.")

    post = next((p for p in database.list_posts() if p['id'] == post_id), None)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    post_content = post['content']
    image_urns = [] # Initialize list for multiple image URNs

    # Check if images were analyzed and stored
    all_image_data = latest_analysis.get("image_data", [])
    all_image_mime_types = latest_analysis.get("image_mime_types", [])

    if all_image_data and all_image_mime_types and len(all_image_data) == len(all_image_mime_types):
        for i, image_data in enumerate(all_image_data):
            mime_type = all_image_mime_types[i]
            try:
                # Upload each image to LinkedIn Assets
                urn = linkedin_client.upload_image_to_linkedin(linkedin_token['access_token'], image_data, mime_type)
                image_urns.append(urn)
                print(f"DEBUG: Image uploaded to LinkedIn, URN: {urn}")
            except Exception as e:
                print(f"Error uploading image {i+1} to LinkedIn Assets: {e}")
                # Continue with other images or return an error
                return RedirectResponse("/?linkedin_error=true&image_upload_error=true", status_code=303)

    try:
        # Pass the list of image_urns to post_linkedin_update
        linkedin_response = linkedin_client.post_linkedin_update(linkedin_token['access_token'], post_content, image_urns)
        
        if "error" in linkedin_response:
            print(f"LinkedIn API Error: {linkedin_response['error']}")
            return RedirectResponse("/?linkedin_error=true", status_code=303)
        else:
            database.mark_posted(post_id)
            return RedirectResponse("/?linkedin_success=true", status_code=303)
    except Exception as e:
        print(f"Error sharing to LinkedIn: {e}")
        return RedirectResponse("/?linkedin_error=true", status_code=303)

@router.get("/export/md")
def export_md():
    """
    Exports all posts as a Markdown file.
    """
    posts = database.list_posts()
    md_content = "# LinkedIn Drafts\n\n"
    for post in posts:
        md_content += f"## Draft (ID: {post['id']}, Status: {post['status']})\n"
        md_content += f"**Created:** {post['created_at']}\n\n"
        md_content += f"{post['content']}\n\n"
        md_content += f"**Hashtags:** {post['hashtags']}\n\n"
        md_content += "---\n\n"
    
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=influra_drafts.md"}
    )

@router.get("/export/csv")
def export_csv():
    """
    Exports all posts as a CSV file.
    """
    posts = database.list_posts()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    if posts:
        writer.writerow(posts[0].keys())
        # Write data
        for post in posts:
            writer.writerow(post.values())
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=influra_drafts.csv"}
    )
