"""Audio metadata scrubber.

Strips ID3/Vorbis Comment/MP4 tags - artist, album, title, comment,
encoder, year, genre and embedded cover art - from MP3, FLAC, OGG and
M4A files while leaving the audio stream untouched.
"""

import shutil

import mutagen

# Maps a human-readable field name to the tag keys (or key prefixes) that
# represent it across the ID3 / Vorbis Comment / MP4 tagging schemes.
FIELDS_OF_INTEREST = {
    "artist": ("TPE1", "artist", "\xa9ART"),
    "album": ("TALB", "album", "\xa9alb"),
    "title": ("TIT2", "title", "\xa9nam"),
    "comment": ("COMM", "comment", "\xa9cmt"),
    "encoder": ("TSSE", "encoder", "\xa9too"),
    "year": ("TDRC", "date", "\xa9day"),
    "genre": ("TCON", "genre", "\xa9gen"),
}


class AudioScrubError(ValueError):
    """Raised when an audio file cannot be opened or processed."""


def strip_audio_metadata(input_path, output_path, ext):
    """Strip metadata from an audio file and write the result to ``output_path``.

    Returns a list of human-readable descriptions of what was removed.
    """
    try:
        shutil.copy(input_path, output_path)
    except OSError as exc:
        raise AudioScrubError(f"could not copy audio file: {exc}") from exc

    try:
        audio = mutagen.File(output_path)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise AudioScrubError(f"could not read audio file: {exc}") from exc

    if audio is None:
        raise AudioScrubError("unrecognized or corrupt audio file")

    stripped_fields = []
    tags = audio.tags
    had_tags = bool(tags)
    has_cover = False

    if tags:
        tag_keys = list(tags.keys())

        for field_name, candidates in FIELDS_OF_INTEREST.items():
            for key in tag_keys:
                if any(key == c or key.startswith(c) for c in candidates):
                    stripped_fields.append(field_name)
                    break

        if ext == "mp3":
            has_cover = any(key.startswith("APIC") for key in tag_keys)
        elif ext == "flac":
            has_cover = bool(getattr(audio, "pictures", None))
        elif ext == "m4a":
            has_cover = "covr" in tag_keys

    if has_cover:
        stripped_fields.append("cover art")

    try:
        if ext == "flac":
            if audio.tags is not None:
                audio.tags.clear()
            audio.clear_pictures()
            audio.save()
        else:
            # MP3 (ID3), OGG (Vorbis Comment) and M4A (MP4 atoms) all support
            # a full tag wipe via delete(), which writes the file in place.
            audio.delete()
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise AudioScrubError(f"failed to strip audio metadata: {exc}") from exc

    if not had_tags:
        stripped_fields.append("No metadata found")
    elif not stripped_fields:
        stripped_fields.append("tags")

    return stripped_fields
