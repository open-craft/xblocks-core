"""
Utility methods for xblock
"""

from functools import cache
from importlib.resources import files


@cache
def read_resource(path):
    """
    Return the text of a file bundled with this package, e.g.
    ``read_resource("static/html/flashcards.html")``.

    Paths are relative to the ``xblock_flashcards`` package. This replaces
    ``pkg_resources.resource_string``, which setuptools no longer ships.
    """
    return files("xblock_flashcards").joinpath(path).read_text(encoding="utf8")
