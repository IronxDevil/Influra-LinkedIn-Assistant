import sqlite3
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