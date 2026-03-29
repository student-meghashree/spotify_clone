# Spotify Clone - Login System Setup Guide

## Features Implemented

✅ **User Authentication System**
- Email/Password registration and login
- Google OAuth 2.0 authentication
- JWT token-based sessions
- User data stored in SQLite database

✅ **Frontend**
- Beautiful Spotify-themed login page
- Toggle between login and registration forms
- Google OAuth button integration
- Music library accessible after login

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Google OAuth

#### Get Google OAuth Credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. **Configure OAuth consent screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type
   - Fill in app name (e.g., "Spotify Clone")
   - Add your email as developer contact
   - Save and continue through all steps
4. **Create credentials:**
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: **Web application**
   - Name: "Spotify Clone Web Client"
   - **Authorized JavaScript origins:** Add `http://localhost:8080`
   - **Authorized redirect URIs:** Add `http://localhost:8080` (if needed)
   - Click "Create"
5. Copy your **Client ID** (looks like: `123456789-abcdef.apps.googleusercontent.com`)

#### Update Configuration:
1. In `main.py`, replace:
   ```python
   GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
   ```
   with your actual Google Client ID

2. In `index.html`, replace:
   ```javascript
   client_id: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com',
   ```
   with your actual Google Client ID

3. **IMPORTANT**: In `main.py`, change the SECRET_KEY to a secure random string:
   ```python
   SECRET_KEY = "your-secret-key-change-this"  # Change this!
   ```

### 3. Initialize Database

```bash
python database.py
```

This creates the SQLite database with `tracks` and `users` tables.

### 4. Run the Backend

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### 5. Open the Frontend

Open `index.html` in your browser:
- Simply double-click the file, or
- Serve it with a local server (recommended):
  ```bash
  python -m http.server 8080
  ```
  Then visit `http://localhost:8080`

### Quick Start (After Initial Setup)

**Option 1: Batch File (Easiest)**
- Double-click `start.bat` in your project folder
- This opens both servers automatically

**Option 2: PowerShell Script**
- Right-click `start.ps1` → "Run with PowerShell"
- This opens both servers automatically

**Option 3: Manual Commands**
```bash
# Terminal 1 - Backend
cd D:\spotify_project
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload

# Terminal 2 - Frontend (in new terminal)
cd D:\spotify_project
python -m http.server 8080
```

### Troubleshooting

If you encounter issues, run the troubleshooting script:
- Double-click `troubleshoot.bat` to diagnose common problems
- It will check Python, virtual environment, dependencies, and database

## API Endpoints

### Authentication

- **POST** `/auth/register` - Register a new user
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password",
    "username": "John Doe"
  }
  ```

- **POST** `/auth/login` - Login with email and password
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```

- **POST** `/auth/google` - Login with Google OAuth (requires user to be registered first)
  ```json
  {
    "token": "google_id_token"
  }
  Response for new users:
  {
    "message": "User not registered",
    "requires_registration": true,
    "google_data": {
      "google_id": "123",
      "email": "user@gmail.com",
      "name": "John Doe"
    }
  }
  ```

- **POST** `/auth/google/register` - Register a new user with Google OAuth data
  ```json
  {
    "google_id": "123",
    "email": "user@gmail.com",
    "username": "johndoe"
  }
  ```

- **GET** `/auth/user?token=YOUR_TOKEN` - Get current user info

### Music Library

- **GET** `/tracks` - List all tracks
- **GET** `/stream/{track_id}` - Stream audio file

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    username TEXT,
    login_method TEXT,
    google_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Tracks Table
```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    artist TEXT,
    file_path TEXT UNIQUE
)
```

## Security Notes

⚠️ **Before production:**

1. Change `SECRET_KEY` to a strong random value
2. Use HTTPS in production
3. Set proper CORS origins instead of `["*"]`
4. Implement rate limiting on login endpoints
5. Use environment variables for sensitive config
6. Add password strength validation
7. Implement email verification
8. Add token refresh mechanism

## Troubleshooting

### Google Login Not Working
- Verify Google Client ID is correct in both `main.py` and `index.html`
- Check CORS settings in `main.py`
- Ensure you're using HTTPS (required for Google OAuth in production)

### Login Token Not Persisting
- Check browser's localStorage is enabled
- Clear browser cache and try again

### Database Errors
- Delete `music.db` and run `python database.py` again
- Ensure you have write permissions in the project directory

## Next Steps

- Add email verification
- Add password reset functionality
- Add user profiles
- Add playback history
- Add favorites/playlist management
- Add search functionality
- Deploy to production (Docker, Heroku, AWS, etc.)
