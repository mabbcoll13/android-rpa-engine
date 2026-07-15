#!/usr/bin/env python3
"""template_match.py - OpenCV template matching for on-screen UI elements.

Given a small cropped "template" image (e.g. a button screenshot), find its
position on the current screen using normalized cross-correlation. Returns the
best center coordinate and the match confidence so the engine can decide
whether the element is actually present.
"""
from __future__ import annotations

import numpy as np
import cv2


class MatchResult:
    def __init__(self, found: bool, cx: int = 0, cy: int = 0, confidence: float = 0.0,
                 box: tuple | None = None):
        self.found = found
        self.cx = cx
        self.cy = cy
        self.confidence = confidence
        self.box = box

    def __repr__(self):
        return f"<Match found={self.found} conf={self.confidence:.2f} cx={self.cx} cy={self.cy}>"


class TemplateMatcher:
    def __init__(self, method: int = cv2.TM_CCOEFF_NORMED, threshold: float = 0.8):
        self.method = method
        self.threshold = threshold

    @staticmethod
    def _load(path: str) -> np.ndarray:
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(path)
        return img

    def match(self, screen: np.ndarray, template_path: str) -> MatchResult:
        template = self._load(template_path)
        th, tw = template.shape[:2]
        sh, sw = screen.shape[:2]
        if th > sh or tw > sw:
            return MatchResult(False)
        result = cv2.matchTemplate(screen, template, self.method)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        x, y = max_loc
        found = bool(max_val >= self.threshold)
        return MatchResult(found, x + tw // 2, y + th // 2, float(max_val),
                           (x, y, tw, th))

    def match_multi(self, screen: np.ndarray, template_path: str) -> list[MatchResult]:
        """Return all locations above threshold (non-maximum suppression)."""
        template = self._load(template_path)
        th, tw = template.shape[:2]
        result = cv2.matchTemplate(screen, template, self.method)
        loc = np.where(result >= self.threshold)
        hits = [MatchResult(True, y + tw // 2, x + th // 2, float(result[y, x]),
                            (x, y, tw, th))
                for y, x in zip(*loc)]
        return hits
