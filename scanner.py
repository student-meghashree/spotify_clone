import os
from mutagen.easyid3 import EasyID3

from database import init_db, insert_track


MUSIC_DIR = "music_library"


def scan_and_populate():
    init_db()

    for root, dirs, files in os.walk(MUSIC_DIR):
        for name in files:
            if name.lower().endswith(".mp3"):
                path = os.path.join(root, name)
                try:
                    tags = EasyID3(path)
                    title = tags.get("title", [os.path.splitext(name)[0]])[0]
                    artist = tags.get("artist", ["Unknown"])[0]
                except Exception:
                    # If metadata can't be read, fall back to filename
                    title = os.path.splitext(name)[0]
                    artist = "Unknown"

                insert_track(title, artist, path)
                print(f"Added: {title} by {artist}")


if __name__ == "__main__":
    scan_and_populate()
