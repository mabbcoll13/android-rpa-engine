#!/usr/bin/env python3
"""ocr.py - OCR helpers (ADB screencap + Tesseract).

Captures the device screen via adb, then runs Tesseract (through pytesseract)
to extract text and word bounding boxes. Falls back gracefully when Tesseract
is not installed so the engine can still run in "template-only" mode.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

try:
    import pytesseract
    _HAVE_TESS = True
except ImportError:  # pragma: no cover
    _HAVE_TESS = False


class OCRError(RuntimeError):
    pass


class OCR:
    def __init__(self, lang: str = "chi_sim+eng", tesseract_cmd: str | None = None):
        self.lang = lang
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    @staticmethod
    def is_available() -> bool:
        return _HAVE_TESS

    @staticmethod
    def load(path: str) -> np.ndarray:
        img = Image.open(path).convert("RGB")
        return np.asarray(img)

    def text(self, image: np.ndarray) -> str:
        """Return the full recognized text of an image array."""
        if not _HAVE_TESS:
            raise OCRError("pytesseract is not installed")
        return pytesseract.image_to_string(Image.fromarray(image), lang=self.lang)

    def words(self, image: np.ndarray) -> list[dict]:
        """Return a list of {'text','x','y','w','h','conf'} for each word."""
        if not _HAVE_TESS:
            raise OCRError("pytesseract is not installed")
        data = pytesseract.image_to_data(
            Image.fromarray(image), lang=self.lang, output_type=pytesseract.Output.DICT)
        out = []
        n = len(data["text"])
        for i in range(n):
            txt = data["text"][i].strip()
            if not txt:
                continue
            out.append({
                "text": txt,
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "conf": data["conf"][i],
            })
        return out

    def find(self, image: np.ndarray, phrase: str) -> dict | None:
        """Locate a phrase; returns the center (cx, cy) of its first match."""
        phrase_l = phrase.lower()
        best = None
        for w in self.words(image):
            if phrase_l in w["text"].lower():
                cx = w["x"] + w["w"] // 2
                cy = w["y"] + w["h"] // 2
                best = {"text": w["text"], "cx": cx, "cy": cy, "box": w}
                break
        return best
