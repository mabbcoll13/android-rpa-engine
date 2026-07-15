#!/usr/bin/env python3
"""engine.py - Core automation loop for the Android RPA engine.

The engine repeatedly performs:  screenshot  ->  perceive  ->  decide  ->  act.
A :class:`Task` supplies the intelligence; the engine supplies the plumbing.

Perception object passed to ``Task.decide`` exposes:
    * ``text``          - full OCR text (str, may be "")
    * ``words``         - list of OCR word boxes
    * ``find(phrase)``  - locate a phrase on screen (returns center or None)
    * ``match(tpl)``    - template-match a UI element (returns MatchResult)

An action returned by ``decide`` is a dict, one of:
    {"type": "tap", "x": int, "y": int}
    {"type": "swipe", "x1":.., "y1":.., "x2":.., "y2":.., "ms":..}
    {"type": "text", "value": "hello"}
    {"type": "key", "code": 3}
    {"type": "wait", "seconds": 1.0}
    {"type": "launch", "package": "com.x"}
    {"type": "stop", "reason": "..."}

Requires: adb; optional pytesseract/opencv for perception. Without Tesseract the
engine still runs in template-only mode if your tasks only call ``match``.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from action import ActionExecutor
from ocr import OCR
from template_match import TemplateMatcher


@dataclass
class Perception:
    text: str = ""
    words: list = field(default_factory=list)
    _ocr: OCR | None = None
    _matcher: TemplateMatcher | None = None

    def find(self, phrase: str):
        if self._ocr is None or self._screen is None:
            return None
        return self._ocr.find(self._screen, phrase)

    def match(self, template_path: str):
        if self._matcher is None or self._screen is None:
            return None
        return self._matcher.match(self._screen, template_path)


class Task:
    """Subclass and implement :meth:`decide`."""

    name: str = "unnamed-task"

    def perceive_hook(self, perception: Perception):
        """Optional: post-process perception before decide()."""

    def decide(self, perception: Perception, step: int) -> dict:
        raise NotImplementedError


class RPAEngine:
    def __init__(self, task: Task, serial: str | None = None,
                 screenshot_path: str = "screen.png", max_steps: int = 50,
                 step_delay: float = 0.5):
        self.task = task
        self.executor = ActionExecutor(serial)
        self.screenshot_path = screenshot_path
        self.max_steps = max_steps
        self.step_delay = step_delay
        self.ocr = OCR() if OCR.is_available() else None
        self.matcher = TemplateMatcher()

    # ----- perception ----------------------------------------------------
    def _perceive(self):
        path = self.executor.screenshot(self.screenshot_path)
        screen = self.ocr.load(path) if self.ocr else None
        percep = Perception(_ocr=self.ocr, _matcher=self.matcher)
        if self.ocr and screen is not None:
            percep._screen = screen
            percep.text = self.ocr.text(screen)
            percep.words = self.ocr.words(screen)
        return percep

    # ----- action dispatch ----------------------------------------------
    def _act(self, action: dict):
        t = action.get("type")
        if t == "tap":
            self.executor.tap(int(action["x"]), int(action["y"]),
                              int(action.get("ms", 0)))
        elif t == "swipe":
            self.executor.swipe(int(action["x1"]), int(action["y1"]),
                                int(action["x2"]), int(action["y2"]),
                                int(action.get("ms", 300)))
        elif t == "text":
            self.executor.input_text(str(action["value"]))
        elif t == "key":
            self.executor.key(int(action["code"]))
        elif t == "wait":
            self.executor.wait(float(action.get("seconds", 1.0)))
        elif t == "launch":
            self.executor.launch(action["package"])
        elif t == "stop":
            return False, action.get("reason", "stopped")
        else:
            raise ValueError(f"unknown action type: {t}")
        return True, None

    # ----- main loop -----------------------------------------------------
    def run(self):
        print(f"[engine] starting task '{self.task.name}' "
              f"(max_steps={self.max_steps}, ocr={'on' if self.ocr else 'off'})")
        for step in range(self.max_steps):
            percep = self._perceive()
            self.task.perceive_hook(percep)
            try:
                action = self.task.decide(percep, step)
            except Exception as e:  # noqa: BLE001
                print(f"[engine] task.decide raised: {e}")
                break
            if action is None:
                print("[engine] task returned None action; stopping")
                break
            print(f"[engine] step {step}: {action}")
            cont, reason = self._act(action)
            if not cont:
                print(f"[engine] stopped: {reason}")
                break
            time.sleep(self.step_delay)
        print("[engine] finished")
