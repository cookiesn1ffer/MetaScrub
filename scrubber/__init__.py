"""Metadata scrubbing package.

Exposes a single entry point, ``scrub_file``, which detects the file
type from its extension and dispatches to the matching scrubber
module (image, document, audio).
"""

from .core import get_file_type, scrub_file

__all__ = ["get_file_type", "scrub_file"]
