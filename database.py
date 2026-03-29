import sqlite3
from hashlib import sha256
from datetime import datetime

DB_PATH = "music.db"


def init_db():
    """Create the tracks and users tables if they don't already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            artist TEXT,
            file_path TEXT UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            username TEXT,
            login_method TEXT,
            google_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id),
            FOREIGN KEY(track_id) REFERENCES tracks(id)
        )
        """
    )
    conn.commit()
    conn.close()


def insert_track(title: str, artist: str, file_path: str):
    """Insert a track into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO tracks (title, artist, file_path) VALUES (?, ?, ?)",
        (title, artist, file_path),
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return sha256(password.encode()).hexdigest()


def create_user(email: str, password: str = None, username: str = None, login_method: str = "email", google_id: str = None) -> dict:
    """Create a new user account."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    password_hash = hash_password(password) if password else None
    
    try:
        cursor.execute(
            """
            INSERT INTO users (email, password_hash, username, login_method, google_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, password_hash, username, login_method, google_id),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "email": email, "username": username, "login_method": login_method}
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user_by_email(email: str):
    """Retrieve a user by email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, username, login_method, google_id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_google_id(google_id: str):
    """Retrieve a user by Google ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, username, login_method FROM users WHERE google_id = ?", (google_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def verify_password(email: str, password: str) -> bool:
    """Verify a user's password."""
    user = get_user_by_email(email)
    if not user:
        return False
    return user.get("password_hash") == hash_password(password)


def create_playlist(user_id: int, name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playlists (user_id, name) VALUES (?, ?)",
        (user_id, name)
    )
    conn.commit()
    playlist_id = cursor.lastrowid
    conn.close()
    return playlist_id


def get_playlists(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, created_at FROM playlists WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_playlist(user_id: int, playlist_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_playlist(user_id: int, playlist_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM playlist_tracks WHERE playlist_id = ?",
        (playlist_id,)
    )
    cursor.execute(
        "DELETE FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, user_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def get_playlist_tracks(user_id: int, playlist_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT p.id FROM playlists p WHERE p.id = ? AND p.user_id = ?",
        (playlist_id, user_id)
    )
    playlist_exists = cursor.fetchone()
    if not playlist_exists:
        conn.close()
        return None

    cursor.execute(
        "SELECT t.id, t.title, t.artist FROM playlist_tracks pt "
        "JOIN tracks t ON pt.track_id = t.id "
        "WHERE pt.playlist_id = ? ORDER BY pt.position",
        (playlist_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_track_to_playlist(user_id: int, playlist_id: int, track_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "SELECT 1 FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
        (playlist_id, track_id)
    )
    if cursor.fetchone():
        conn.close()
        return True

    cursor.execute(
        "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id = ?",
        (playlist_id,)
    )
    position = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES (?, ?, ?)",
        (playlist_id, track_id, position)
    )
    conn.commit()
    conn.close()
    return True


def remove_track_from_playlist(user_id: int, playlist_id: int, track_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM playlists WHERE id = ? AND user_id = ?",
        (playlist_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
        (playlist_id, track_id)
    )
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
