"""Image metadata scrubber.

Strips EXIF data (including the GPS IFD, camera make/model, software
tags and timestamps) from JPEG, PNG, TIFF and WEBP images while
preserving pixel data, dimensions and image mode.
"""

from PIL import Image

# EXIF tag ID for the GPS IFD pointer.
GPS_IFD_TAG = 0x8825

# EXIF tags that are explicitly called out by the scrubbing spec.
TAGS_OF_INTEREST = {
    0x010F: "Make",
    0x0110: "Model",
    0x0131: "Software",
    0x0132: "DateTime",
    0x9003: "DateTimeOriginal",
    0x013B: "Artist",
    0x8298: "Copyright",
}

# Non-EXIF metadata chunks Pillow may surface via Image.info.
INFO_KEYS_OF_INTEREST = ("icc_profile", "comment", "description")


class ImageScrubError(ValueError):
    """Raised when an image file cannot be opened or processed."""


def strip_image_metadata(input_path, output_path):
    """Strip all metadata from an image and write the result to ``output_path``.

    Returns a list of human-readable descriptions of what was removed.
    """
    try:
        img = Image.open(input_path)
        img.load()
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise ImageScrubError(f"could not open image: {exc}") from exc

    fmt = img.format
    stripped_fields = []

    try:
        exif = img.getexif()
    except Exception:  # noqa: BLE001 - some files have malformed EXIF blocks
        exif = None

    if exif:
        if GPS_IFD_TAG in exif:
            stripped_fields.append("GPS (latitude/longitude/altitude/timestamp)")

        for tag_id, name in TAGS_OF_INTEREST.items():
            if tag_id in exif:
                stripped_fields.append(name)

        if len(exif) > 0:
            stripped_fields.append("EXIF metadata")

    for key in INFO_KEYS_OF_INTEREST:
        if key in img.info:
            stripped_fields.append(key)

    mode = img.mode
    size = img.size
    pixel_data = list(img.getdata())

    # Rebuild the image from raw pixel data only. A brand new Image has an
    # empty .info dict, so no EXIF/ICC/text chunks survive into the clean copy.
    clean_img = Image.new(mode, size)

    if mode == "P":
        palette = img.getpalette()
        if palette:
            clean_img.putpalette(palette)

    clean_img.putdata(pixel_data)

    # Preserve transparency info (not privacy-sensitive) so PNGs/WEBPs with
    # alpha via a palette index keep rendering correctly.
    if "transparency" in img.info:
        clean_img.info["transparency"] = img.info["transparency"]

    save_kwargs = {}
    if fmt:
        save_kwargs["format"] = fmt
    if fmt == "JPEG":
        save_kwargs["quality"] = 95
        save_kwargs["subsampling"] = 0

    try:
        clean_img.save(output_path, **save_kwargs)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise ImageScrubError(f"could not save cleaned image: {exc}") from exc

    if not stripped_fields:
        stripped_fields.append("No metadata found")

    return stripped_fields
