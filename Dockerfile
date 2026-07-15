FROM python:3.11-slim

# System deps: OpenCV/Tesseract need shared libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-chi-sim \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY examples/ ./examples/

# adb is provided by mounting the host's platform-tools or installing via your
# own base image; the engine raises a clear error if adb is missing.

CMD ["python", "examples/wechat_auto/wechat_auto.py"]
