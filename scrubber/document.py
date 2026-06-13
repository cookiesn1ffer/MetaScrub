"""DOCX metadata scrubber.

Strips author, last_modified_by, company, revision, created and
modified properties from a .docx file while leaving all document
content, styles and formatting untouched.
"""

import os
import re
import zipfile
from datetime import datetime, timezone

from docx import Document

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Regex patterns to blank out app.xml fields that python-docx does not
# expose via CoreProperties (docProps/app.xml, not docProps/core.xml).
_APP_XML_TAGS = ("Company", "Manager")


class DocumentScrubError(ValueError):
    """Raised when a .docx file cannot be opened or processed."""


def strip_document_metadata(input_path, output_path):
    """Strip metadata from a .docx file and write the result to ``output_path``.

    Returns a list of human-readable descriptions of what was removed.
    """
    try:
        doc = Document(input_path)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise DocumentScrubError(f"could not open document: {exc}") from exc

    stripped_fields = []
    cp = doc.core_properties

    if cp.author:
        stripped_fields.append("author")
    cp.author = ""

    if cp.last_modified_by:
        stripped_fields.append("last_modified_by")
    cp.last_modified_by = ""

    if cp.revision and cp.revision != 1:
        stripped_fields.append("revision")
    try:
        cp.revision = 1
    except ValueError:
        # Some python-docx versions reject values < 1; 1 is the minimum
        # representable "blank" revision.
        pass

    if cp.created:
        stripped_fields.append("created")
    cp.created = EPOCH

    if cp.modified:
        stripped_fields.append("modified")
    cp.modified = EPOCH

    try:
        doc.save(output_path)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a 422
        raise DocumentScrubError(f"could not save cleaned document: {exc}") from exc

    if _strip_app_properties(output_path):
        stripped_fields.append("company")

    if not stripped_fields:
        stripped_fields.append("No metadata found")

    return stripped_fields


def _strip_app_properties(docx_path):
    """Blank out Company/Manager fields in docProps/app.xml in-place.

    python-docx does not expose docProps/app.xml, so it is edited directly
    by rewriting the zip archive that backs the .docx file. Returns True if
    any field was changed.
    """
    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            names = zin.namelist()
            if "docProps/app.xml" not in names:
                return False
            contents = {name: zin.read(name) for name in names}
    except (zipfile.BadZipFile, OSError) as exc:
        raise DocumentScrubError(f"could not read cleaned document: {exc}") from exc

    changed = False
    app_xml = contents["docProps/app.xml"].decode("utf-8")

    for tag in _APP_XML_TAGS:
        pattern = rf"<{tag}>.*?</{tag}>"
        replacement = f"<{tag}></{tag}>"
        new_xml, count = re.subn(pattern, replacement, app_xml, flags=re.DOTALL)
        if count:
            changed = True
        app_xml = new_xml

    if not changed:
        return False

    contents["docProps/app.xml"] = app_xml.encode("utf-8")

    tmp_path = docx_path + ".tmp"
    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name, data in contents.items():
                zout.writestr(name, data)
        os.replace(tmp_path, docx_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return True
