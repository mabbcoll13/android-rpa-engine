# Android RPA Engine

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small, dependency-light **Robotic Process Automation** engine for Android.
It drives a real device/emulator through `adb` using a
**screenshot → perceive → decide → act** loop, with pluggable perception
(OCR + template matching) and a simple task interface.

> 📧 Contact / 联系方式: **qtphone.com**

---

## Architecture

```
src/
├── engine.py          # RPAEngine + Task + Perception (the loop)
├── action.py          # ActionExecutor: tap / swipe / text / key / launch
├── ocr.py             # OCR: adb screencap + Tesseract (text + word boxes)
├── template_match.py  # OpenCV template matching for UI elements
└── __init__.py
examples/wechat_auto/  # Worked example: open WeChat and send a greeting
Dockerfile + docker-compose.yml
```

### The loop
```
for step in range(max_steps):
    screen = adb.screencap()
    perception = perceive(screen)      # OCR text + template matches
    action = task.decide(perception)   # tap / swipe / text / wait / stop
    executor.act(action)
```

## Usage

```bash
pip install -r requirements.txt
# ensure `adb` is on PATH and a device is connected
python examples/wechat_auto/wechat_auto.py
```

Or containerised (shares the host network so the device is reachable):

```bash
docker compose up --build
```

## Writing your own task

```python
from src.engine import RPAEngine, Task, Perception

class MyTask(Task):
    name = "demo"
    def decide(self, p: Perception, step: int) -> dict:
        hit = p.find("登录")          # OCR lookup
        if hit:
            return {"type": "tap", "x": hit["cx"], "y": hit["cy"]}
        tpl = p.match("templates/ok.png")
        if tpl and tpl.found:
            return {"type": "tap", "x": tpl.cx, "y": tpl.cy}
        return {"type": "wait", "seconds": 1.0}

RPAEngine(MyTask(), max_steps=30).run()
```

## Disclaimer

For **automation of apps you own or are authorized to automate**. Respect each
app's terms of service and applicable law.

---

## About & Contact

**QTPhone** — Global Independent IP Cloud Android Devices

- 🌐 Official Website: [https://www.qtphone.com/](https://www.qtphone.com/)
- 💬 WhatsApp: **@along915**
- 📧 Gmail: **ailong9281@gmail.com**
- ✈️ Telegram: **@Alongyun**