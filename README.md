# Spotify Clone (local)

Quick steps to run the backend and frontend locally.

Prerequisites
- Python 3.10+ (or your current project's Python)

Steps

1. Activate your virtual environment (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

Or (cmd):

```cmd
.\venv\Scripts\activate.bat
```

2. Install dependencies (if not already installed):

```powershell
pip install fastapi uvicorn mutagen
```

3. Scan your `music_library` to populate `music.db`:

```powershell
python scanner.py
```

4. Start the FastAPI server (default port 8000):

```powershell
uvicorn main:app --reload
```

CORS is enabled in `main.py`, so the frontend can fetch across ports.

5. Serve the frontend (recommended) from the project root so fetch works reliably:

```powershell
python -m http.server 3000
```

6. Open the frontend in your browser:

```
http://127.0.0.1:3000/index.html
```

Notes
- If you run the API on a different port, update the `BASE` constant in `index.html` accordingly (default is `http://127.0.0.1:8000`).
- If audio files are missing from disk, `/stream/{id}` will return `404 Audio file not found`.

Enjoy! 🎧
