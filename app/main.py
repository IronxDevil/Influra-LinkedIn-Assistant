from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.db.database import init_db, list_posts
from app.routers import profile, trends, posts, auth, images # Added images
from app.state import latest_analysis
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes resources on startup and cleans up on shutdown."""
    init_db()
    yield


app = FastAPI(
    title="Influra MVP",
    description="A minimal working app to generate LinkedIn content from profiles and trends.",
    version="0.1.0",
    lifespan=lifespan
)

# Add Session Middleware for OAuth2 flow
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Include routers
app.include_router(profile.router)
app.include_router(trends.router)
app.include_router(posts.router)
app.include_router(auth.router)
app.include_router(images.router) # Include images router

templates = Jinja2Templates(directory="app/templates")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Serves the main HTML dashboard, passing in current state."""
    saved_posts = list_posts()
    context = {
        "request": request,
        "profile_summary": latest_analysis.get("profile_summary"),
        "trend_insights": latest_analysis.get("trend_insights"),
        "generated_post": latest_analysis.get("generated_post"),
        "saved_posts": saved_posts,
        "image_analysis": latest_analysis.get("image_analysis"), # Pass image analysis to template
    }
    return templates.TemplateResponse("index.html", context)