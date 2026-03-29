from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sqlite3
from typing import Generator, Optional
import jwt
from datetime import datetime, timedelta
from database import (
    init_db, insert_track, get_user_by_email, get_user_by_google_id,
    create_user, verify_password, create_playlist, get_playlists,
    get_playlist, delete_playlist, get_playlist_tracks,
    add_track_to_playlist, remove_track_from_playlist
)
import requests
import os

DB_PATH = "music.db"
SECRET_KEY = os.getenv("SECRET_KEY", "spotify-clone-secure-key-2026-change-this-in-production")  # Change this to a secure key
ALGORITHM = "HS256"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "821874390575-56kprcb31knja35g3rc8skkrcg94h25u.apps.googleusercontent.com")  # Set your Google OAuth Client ID here

# Initialize database on startup
init_db()

app = FastAPI()

# Allow CORS from any origin so the frontend can fetch across ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files under /static; avoid overriding API routes
app.mount("/static", StaticFiles(directory="."), name="static")

# Route root to index.html
@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
    return FileResponse("index.html")

# Pydantic Models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class GoogleLoginRequest(BaseModel):
    token: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_access_token(user_id: int, email: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> dict:
    """Verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None

def get_current_user(token: Optional[str] = None) -> dict:
    """Get the current user from the token."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# Authentication Endpoints
@app.post("/auth/register")
def register(request: RegisterRequest):
    """Register a new user."""
    user = get_user_by_email(request.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = create_user(request.email, request.password, request.username, "email")
    if not new_user:
        raise HTTPException(status_code=400, detail="Failed to create user")
    
    token = create_access_token(new_user["id"], new_user["email"])
    return {
        "message": "User registered successfully",
        "token": token,
        "user": new_user
    }

@app.post("/auth/login")
def login(request: LoginRequest):
    """Login with email and password."""
    user = get_user_by_email(request.email)
    if not user or not verify_password(request.email, request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user["id"], user["email"])
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"]
        }
    }

@app.post("/auth/google")
def google_login(request: GoogleLoginRequest):
    """Login with Google OAuth - requires user to be registered first."""
    try:
        # Verify the token with Google
        google_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
        google_response = requests.get(f"{google_url}?id_token={request.token}")
        
        if google_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        google_data = google_response.json()
        google_id = google_data.get("sub")
        email = google_data.get("email")
        name = google_data.get("name")
        
        # Check if user exists with Google ID
        user = get_user_by_google_id(google_id)
        if user:
            # User exists with Google ID, log them in
            token = create_access_token(user["id"], user["email"])
            return {
                "message": "Google login successful",
                "token": token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"]
                }
            }
        
        # Check if user exists with email (maybe they registered with email first)
        user = get_user_by_email(email)
        if user:
            # User exists with email, link Google account and log them in
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET google_id = ?, login_method = ? WHERE email = ?",
                (google_id, "google", email)
            )
            conn.commit()
            conn.close()
            
            token = create_access_token(user["id"], user["email"])
            return {
                "message": "Google login successful",
                "token": token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"]
                }
            }
        
        # User doesn't exist - return Google data for registration
        return {
            "message": "User not registered",
            "requires_registration": True,
            "google_data": {
                "google_id": google_id,
                "email": email,
                "name": name
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/google/register")
def google_register(request: dict):
    """Register a new user with Google OAuth data."""
    google_id = request.get("google_id")
    email = request.get("email")
    username = request.get("username")
    
    if not google_id or not email or not username:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Check if user already exists
    existing_user = get_user_by_email(email) or get_user_by_google_id(google_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user with Google data
    new_user = create_user(email, username=username, login_method="google", google_id=google_id)
    if not new_user:
        raise HTTPException(status_code=400, detail="Failed to create user")
    
    token = create_access_token(new_user["id"], new_user["email"])
    return {
        "message": "User registered with Google successfully",
        "token": token,
        "user": new_user
    }

@app.get("/auth/user")
def get_user(token: str):
    """Get current user info."""
    payload = get_current_user(token)
    user = get_user_by_email(payload["email"])
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"]
    }

@app.get("/tracks")
def list_tracks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, artist FROM tracks")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/playlists")
def list_playlists(token: str):
    user = get_current_user(token)
    user_id = int(user["sub"])
    playlists = get_playlists(user_id)
    return playlists


@app.post("/playlists")
def create_new_playlist(token: str, body: dict):
    user = get_current_user(token)
    user_id = int(user["sub"])
    name = body.get("name")
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Playlist name is required")
    playlist_id = create_playlist(user_id, name.strip())
    return {"id": playlist_id, "name": name.strip()}


@app.get("/playlists/{playlist_id}")
def get_playlist_detail(playlist_id: int, token: str):
    user = get_current_user(token)
    user_id = int(user["sub"])
    playlist = get_playlist(user_id, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    tracks = get_playlist_tracks(user_id, playlist_id)
    return {"id": playlist_id, "name": playlist["name"], "tracks": tracks}


@app.delete("/playlists/{playlist_id}")
def delete_existing_playlist(playlist_id: int, token: str):
    user = get_current_user(token)
    user_id = int(user["sub"])
    success = delete_playlist(user_id, playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"message": "Playlist deleted"}


@app.post("/playlists/{playlist_id}/tracks")
def add_track(playlist_id: int, token: str, body: dict):
    user = get_current_user(token)
    user_id = int(user["sub"])
    track_id = body.get("track_id")
    if not track_id:
        raise HTTPException(status_code=400, detail="Track ID is required")
    if not add_track_to_playlist(user_id, playlist_id, int(track_id)):
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"message": "Track added"}


@app.delete("/playlists/{playlist_id}/tracks/{track_id}")
def remove_track(playlist_id: int, track_id: int, token: str):
    user = get_current_user(token)
    user_id = int(user["sub"])
    if not remove_track_from_playlist(user_id, playlist_id, track_id):
        raise HTTPException(status_code=404, detail="Playlist or track not found")
    return {"message": "Track removed"}


@app.post("/playlists/from_mood")
def create_playlist_from_mood(token: str, body: dict):
    user = get_current_user(token)
    user_id = int(user["sub"])
    name = body.get("name")
    track_ids = body.get("track_ids")
    if not name or not track_ids or not isinstance(track_ids, list):
        raise HTTPException(status_code=400, detail="Name and track_ids required")
    playlist_id = create_playlist(user_id, name.strip())
    for i, tid in enumerate(track_ids):
        add_track_to_playlist(user_id, playlist_id, int(tid))
    return {"id": playlist_id, "name": name.strip(), "track_ids": track_ids}


@app.post("/auth/logout")
def logout(token: str):
    # No server-side state for JWT; client should clear token.
    return {"message": "Logout successful"}


@app.get("/stream/{track_id}")
def stream_track(track_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM tracks WHERE id = ?", (track_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Track not found")

    file_path = row[0]
    try:
        file_obj = open(file_path, "rb")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Audio file not found")

    def iterfile() -> Generator[bytes, None, None]:
        with file_obj:
            while chunk := file_obj.read(1024 * 1024):
                yield chunk

    return StreamingResponse(iterfile(), media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
