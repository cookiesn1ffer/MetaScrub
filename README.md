# >_ MetaScrub

Strip hidden metadata from images, documents & audio. Nothing leaves your machine.

![MetaScrub Screenshot](screenshot.png)

## Supported formats
- **Images** — JPG, PNG, TIFF, WEBP (strips EXIF, GPS, camera make/model)
- **Documents** — DOCX (strips author, company, revision, timestamps)
- **Audio** — MP3, FLAC, OGG, M4A (strips ID3 tags, cover art)

## Desktop app (PyQt6)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements_gui.txt
python gui.py
```

### Build a standalone executable
```bash
python build.py
# Output: dist/MetaScrub-windows.exe (or dist/MetaScrub-linux)
```

## Web app (Flask)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

## Stack
- PyQt6 — desktop UI
- Flask — web UI
- Pillow — image EXIF strip
- python-docx — document metadata strip
- mutagen — audio tag strip
- SQLite — job history

## License
MIT
