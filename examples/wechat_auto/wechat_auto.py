#!/usr/bin/env python3
"""wechat_auto.py - Example RPA task: open WeChat and send a greeting.

This shows the engine's perceive -> decide -> act loop in practice. It:
  1. launches com.tencent.mm
  2. waits for the UI to settle
  3. taps the search icon (by template, falling back to a fixed coordinate)
  4. types a message and sends it

Adjust the template images / coordinates for your device resolution.

Run:  python examples/wechat_auto/wechat_auto.py
"""
from __future__ import annotations

import os
import sys

# Allow running both as a module and a script.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.engine import RPAEngine, Task, Perception
from src.action import ActionError

WECHAT_PKG = "com.tencent.mm"
SEARCH_TPL = os.path.join(os.path.dirname(__file__), "templates", "search.png")


class WeChatAutoTask(Task):
    name = "wechat-auto-greet"
    _phase = 0

    def __init__(self, message: str = "Hello from RPA engine (qtphone.com)"):
        self.message = message

    def perceive_hook(self, p: Perception):
        # Convenience: keep last seen text on the task for decide() to use.
        self._screen_text = p.text
        self._search = p.match(SEARCH_TPL) if os.path.exists(SEARCH_TPL) else None

    def decide(self, p: Perception, step: int) -> dict:
        # Phase 0: launch
        if self._phase == 0:
            self._phase = 1
            return {"type": "launch", "package": WECHAT_PKG}
        # Phase 1: settle, then find search
        if self._phase == 1:
            self._phase = 2
            return {"type": "wait", "seconds": 3.0}
        if self._phase == 2:
            if self._search and self._search.found:
                self._phase = 3
                return {"type": "tap", "x": self._search.cx, "y": self._search.cy}
            # fallback coordinate (typical 1080p location)
            self._phase = 3
            return {"type": "tap", "x": 980, "y": 160}
        if self._phase == 3:
            self._phase = 4
            return {"type": "text", "value": self.message}
        if self._phase == 4:
            self._phase = 5
            return {"type": "key", "code": 66}  # KEYCODE_ENTER
        return {"type": "stop", "reason": "greeting sent"}


def main():
    task = WeChatAutoTask()
    engine = RPAEngine(task, max_steps=12, step_delay=1.0)
    try:
        engine.run()
    except ActionError as e:
        print("ADB error:", e)
        print("Make sure a device is connected and 'adb' is on PATH.")


if __name__ == "__main__":
    main()
