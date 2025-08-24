import sqlite3
import json
from app.config import settings


def get_conn():
    """Returns a sqlite3 connection object to the database."""
    conn = sqlite3.connect(settings.DATABASE_URL)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn


def init_db():
    """
    Initializes the database by creating tables from the schema.sql file.
    This function is idempotent and can be called safely on startup.
    """
    conn = get_conn()
    with open('app/db/schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized.")

# --- Post Functions ---

def insert_post(content: str, hashtags: str, status: str = 'draft') -> int:
    """Inserts a new post into the database."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (content, hashtags, status) VALUES (?, ?, ?)",
        (content, hashtags, status)
    )
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


def list_posts() -> list[dict]:
    """Lists all posts from the database."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts


def mark_posted(post_id: int):
    """Marks a post as posted and sets the posted_at timestamp."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE posts SET status = 'posted', posted_at = CURRENT_TIMESTAMP WHERE id = ?",
        (post_id,)
    )
    conn.commit()
    conn.close()

def delete_posts(post_ids: list[int]):
    """Deletes one or more posts from the database by their IDs."""
    if not post_ids:
        return
    conn = get_conn()
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in post_ids)
    query = f"DELETE FROM posts WHERE id IN ({placeholders})"
    cursor.execute(query, post_ids)
    conn.commit()
    conn.close()

# --- User Profile Functions ---

def upsert_user_profile(user_id: str, profile_summary: dict):
    """Inserts or updates a user's profile summary."""
    conn = get_conn()
    cursor = conn.cursor()
    profile_summary_json = json.dumps(profile_summary)
    cursor.execute(
        """INSERT INTO user_profiles (user_id, profile_summary_json, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
           profile_summary_json = excluded.profile_summary_json,
           updated_at = CURRENT_TIMESTAMP""",
        (user_id, profile_summary_json)
    )
    conn.commit()
    conn.close()

def get_user_profile(user_id: str) -> dict | None:
    """Retrieves a user's profile summary by their ID."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT profile_summary_json FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['profile_summary_json'])
    return None

# --- Trend Functions ---

def add_trend(topic: str, source_url: str):
    """Adds a new trend to the database, ignoring duplicates."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO trends (topic, source_url) VALUES (?, ?)",
        (topic, source_url)
    )
    conn.commit()
    conn.close()

def get_latest_trends(limit: int = 6) -> list[dict]:
    """Lists the most recent trends from the database."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT topic, source_url FROM trends ORDER BY created_at DESC LIMIT ?", (limit,))
    trends = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return trends