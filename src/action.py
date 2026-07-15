#!/usr/bin/env python3
"""action.py - ADB action executor for the Android RPA engine.

Wraps the most common `adb shell input` commands plus screenshot capture.
All methods are no-ops safe: if `adb` is missing they raise a clear error
rather than silently failing.

Requires: adb on PATH and a device connected (or set ADB_SERIAL).
"""
from __future__ import annotations

import os
import subprocess
import time

DEFAULT_SCREENSHOT = "/sdcard/rpa_screenshot.png"


class ActionError(RuntimeError):
    pass


class ActionExecutor:
    def __init__(self, serial: str | None = None, adb_path: str = "adb"):
        self.serial = serial or os.environ.get("ADB_SERIAL")
        self.adb = adb_path

    # ----- low level -----------------------------------------------------
    def _adb(self, *args: str) -> str:
        cmd = [self.adb]
        if self.serial:
            cmd += ["-s", self.serial]
        cmd += list(args)
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            raise ActionError(f"adb not found at '{self.adb}'. Install platform-tools.")
        except subprocess.TimeoutExpired:
            raise ActionError(f"adb command timed out: {cmd}")
        if out.returncode != 0:
            raise ActionError(f"adb {args} failed: {out.stderr.strip()}")
        return out.stdout

    # ----- device helpers -------------------------------------------------
    def devices(self) -> list[str]:
        lines = self._adb("devices").splitlines()[1:]
        return [ln.split()[0] for ln in lines if ln.strip() and "device" in ln]

    def screenshot(self, local_path: str = "screenshot.png") -> str:
        """Capture a screenshot and pull it to `local_path`. Returns the path."""
        remote = DEFAULT_SCREENSHOT
        self._adb("shell", "screencap", "-p", remote)
        self._adb("pull", remote, local_path)
        return local_path

    def tap(self, x: int, y: int, duration_ms: int = 0):
        if duration_ms > 0:
            self._adb("shell", "input", "swipe", str(x), str(y), str(x), str(y),
                      str(duration_ms))
        else:
            self._adb("shell", "input", "tap", str(x), str(y))

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300):
        self._adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2),
                  str(duration_ms))

    def input_text(self, text: str):
        # adb input text is picky about spaces / special chars -> use %s encoding
        safe = text.replace(" ", "%s")
        self._adb("shell", "input", "text", safe)

    def key(self, code: int):
        self._adb("shell", "input", "keyevent", str(code))

    def home(self):
        self.key(3)

    def back(self):
        self.key(4)

    def wait(self, seconds: float):
        time.sleep(seconds)

    def launch(self, package: str, activity: str | None = None):
        if activity:
            self._adb("shell", "am", "start", "-n", f"{package}/{activity}")
        else:
            self._adb("shell", "monkey", "-p", package, "-c",
                      "android.intent.category.LAUNCHER", "1")
