"""
Name: fleep.py
Description: File format determination library
Author: Mykyta Paliienko
License: MIT
"""

import json
from pathlib import Path

with (Path(__file__).parent / "data.json").open(encoding="utf-8") as data_file:
    data = json.load(data_file)


class Info:
    """
    Generates object with given arguments

    Args:
        types (list) -> list of file types
        extensions (list) -> list of file extensions
        mimes (list) -> list of file MIME types

    Returns:
        (<class 'fleep.Info'>) -> Class instance
    """

    def __init__(self, types: list, extensions: list, mimes: list):
        self.types = types
        self.extensions = extensions
        self.mimes = mimes

    def type_matches(self, type_: str):
        """Checks if file type matches with given type"""
        return type_ in self.types

    def extension_matches(self, extension: str):
        """Checks if file extension matches with given extension"""
        return extension in self.extensions

    def mime_matches(self, mime: str):
        """Checks if file MIME type matches with given MIME type"""
        return mime in self.mimes


def get(obj: bytes):
    """
    Determines file format and picks suitable file types, extensions and MIME types

    Args:
        obj (bytes) -> byte sequence (128 bytes are enough)

    Returns:
        (<class 'fleep.Info'>) -> Class instance
    """

    if not isinstance(obj, bytes):
        raise TypeError("object type must be bytes")

    stream = " ".join([f"{byte:02X}" for byte in obj])

    types = {}
    extensions = {}
    mimes = {}
    for element in data:
        for signature in element["signature"]:
            offset = element["offset"] * 2 + element["offset"]
            if signature == stream[offset : len(signature) + offset]:
                types[element["type"]] = len(signature)
                extensions[element["extension"]] = len(signature)
                mimes[element["mime"]] = len(signature)
    return Info(
        sorted(types, key=lambda x: types.get(x, False), reverse=True),
        sorted(extensions.keys(), key=lambda x: extensions.get(x, False), reverse=True),
        sorted(mimes.keys(), key=lambda x: mimes.get(x, False), reverse=True),
    )


def supported_types():
    """Returns a list of supported file types"""
    return sorted({x["type"] for x in data})


def supported_extensions():
    """Returns a list of supported file extensions"""
    return sorted({x["extension"] for x in data})


def supported_mimes():
    """Returns a list of supported file MIME types"""
    return sorted({x["mime"] for x in data})
