"""File type detection and scrubber dispatch."""

from .audio import strip_audio_metadata
from .document import strip_document_metadata
from .image import strip_image_metadata

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "tiff", "webp"}
DOCUMENT_EXTENSIONS = {"docx"}
AUDIO_EXTENSIONS = {"mp3", "flac", "ogg", "m4a"}


def get_extension(filename):
    """Return the lowercase extension of ``filename`` (without the dot)."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def get_file_type(filename):
    """Classify ``filename`` as 'image', 'document', 'audio' or None."""
    ext = get_extension(filename)
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return None


def scrub_file(input_path, output_path, filename):
    """Scrub metadata from ``input_path``, writing the result to ``output_path``.

    Returns a tuple of ``(file_type, stripped_fields)``.

    Raises ``ValueError`` if the file type is unsupported or the file is
    corrupt/unprocessable.
    """
    ext = get_extension(filename)
    file_type = get_file_type(filename)

    if file_type == "image":
        stripped_fields = strip_image_metadata(input_path, output_path)
    elif file_type == "document":
        stripped_fields = strip_document_metadata(input_path, output_path)
    elif file_type == "audio":
        stripped_fields = strip_audio_metadata(input_path, output_path, ext)
    else:
        raise ValueError(f"unsupported file type: .{ext}")

    return file_type, stripped_fields
