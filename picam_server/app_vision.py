import sys
import types
import os
import time
import json
import numpy as np
import cv2
from flask import Flask, render_template, jsonify, send_from_directory, request

app = Flask(__name__, template_folder="templates")

PHOTO_DIR    = os.path.join(os.path.dirname(__file__), "photos_vision_raw")
RESULT_DIR   = os.path.join(os.path.dirname(__file__), "photos_vision_result")
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# ── Default HSV tuning parameters ──────────────────────────────────────────
# Each material: [h_low, s_low, v_low, h_high, s_high, v_high, min_radius, max_radius]
DEFAULT_PARAMS = {
    "copper": {
        "h_low": 5,  "s_low": 80,  "v_low": 80,
        "h_high": 22, "s_high": 255, "v_high": 255,
        "min_r": 8, "max_r": 80,
        "color_bgr": [30, 80, 200]   # drawn box color
    },
    "aluminium": {
        "h_low": 0,  "s_low": 0,   "v_low": 160,
        "h_high": 180, "s_high": 55, "v_high": 255,
        "min_r": 8, "max_r": 80,
        "color_bgr": [200, 200, 200]
    },
    "iron": {
        "h_low": 0,  "s_low": 0,   "v_low": 40,
        "h_high": 180, "s_high": 50, "v_high": 140,
        "min_r": 8, "max_r": 80,
        "color_bgr": [120, 120, 120]
    }
}

# Runtime params (can be updated via /update_params)
params = json.loads(json.dumps(DEFAULT_PARAMS))


def get_camera():
    class MagicMock:
        def __getattr__(self, name):
            return self

    magic_instance = MagicMock()
    fake_kms = types.ModuleType("pykms")
    fake_kms.PixelFormat = magic_instance
    fake_kms.PixelFormats = magic_instance
    sys.modules["pykms"] = fake_kms
    sys.modules["kms"] = fake_kms

    from picamzero import Camera
    return Camera()


def detect_balls(image_path, out_path, current_params):
    """
    For each material:
      1. Apply HSV mask to isolate the material's color range
      2. Morphological cleanup to reduce gravel noise
      3. Hough Circle Transform to find circular shapes
      4. Draw bounding box + label on detections
    Returns list of detections.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Could not read image: {image_path}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    result_img = img.copy()
    detections = []

    for material, p in current_params.items():
        lower = np.array([p["h_low"],  p["s_low"],  p["v_low"]],  dtype=np.uint8)
        upper = np.array([p["h_high"], p["s_high"], p["v_high"]], dtype=np.uint8)

        # Color mask
        mask = cv2.inRange(hsv, lower, upper)

        # Special case: iron/aluminium wrap around hue=0 is already handled
        # by wide hue range 0-180; copper uses narrow orange band

        # Morphological ops — remove gravel speckle, fill ball interior
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Blur before Hough (required for good circle detection)
        blurred = cv2.GaussianBlur(mask, (9, 9), 2)

        min_r = int(p["min_r"])
        max_r = int(p["max_r"])
        img_h, img_w = img.shape[:2]

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(20, min_r * 2),
            param1=50,
            param2=25,
            minRadius=min_r,
            maxRadius=max_r
        )

        color_bgr = tuple(p["color_bgr"])

        if circles is not None:
            circles = np.round(circles[0]).astype(int)
            for (cx, cy, r) in circles:
                # Bounding box from circle
                x1 = max(0, cx - r)
                y1 = max(0, cy - r)
                x2 = min(img_w, cx + r)
                y2 = min(img_h, cy + r)

                # Draw circle outline
                cv2.circle(result_img, (cx, cy), r, color_bgr, 2)
                # Draw centre dot
                cv2.circle(result_img, (cx, cy), 3, color_bgr, -1)
                # Draw bounding box
                cv2.rectangle(result_img, (x1, y1), (x2, y2), color_bgr, 1)

                # Label
                label = material.upper()
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                label_y = max(y1, th + 6)
                cv2.rectangle(result_img, (x1, label_y - th - 6), (x1 + tw + 6, label_y), color_bgr, -1)
                cv2.putText(result_img, label, (x1 + 3, label_y - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)

                detections.append({
                    "material": material,
                    "center": [int(cx), int(cy)],
                    "radius": int(r),
                    "box": [int(x1), int(y1), int(x2), int(y2)]
                })

    cv2.imwrite(out_path, result_img)
    return detections


@app.route("/")
def index():
    return render_template("index_vision.html")


@app.route("/capture", methods=["POST"])
def capture():
    try:
        timestamp = int(time.time() * 1000)
        raw_filename    = f"raw_{timestamp}.jpg"
        result_filename = f"result_{timestamp}.jpg"
        raw_path    = os.path.join(PHOTO_DIR,  raw_filename)
        result_path = os.path.join(RESULT_DIR, result_filename)

        cam = get_camera()
        cam.take_photo(raw_path)

        t0 = time.time()
        detections = detect_balls(raw_path, result_path, params)
        elapsed = round(time.time() - t0, 3)

        return jsonify({
            "success": True,
            "raw": raw_filename,
            "result": result_filename,
            "detections": detections,
            "elapsed": elapsed
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    """Re-run detection on the last raw image with current params (for live tuning)."""
    try:
        raws = sorted(
            [f for f in os.listdir(PHOTO_DIR) if f.startswith("raw_")],
            reverse=True
        )
        if not raws:
            return jsonify({"success": False, "error": "No photos yet"}), 400

        raw_path = os.path.join(PHOTO_DIR, raws[0])
        timestamp = int(time.time() * 1000)
        result_filename = f"result_{timestamp}.jpg"
        result_path = os.path.join(RESULT_DIR, result_filename)

        t0 = time.time()
        detections = detect_balls(raw_path, result_path, params)
        elapsed = round(time.time() - t0, 3)

        return jsonify({
            "success": True,
            "raw": raws[0],
            "result": result_filename,
            "detections": detections,
            "elapsed": elapsed
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/update_params", methods=["POST"])
def update_params():
    """Receive updated tuning params from the UI."""
    global params
    try:
        data = request.get_json()
        for material in ["copper", "aluminium", "iron"]:
            if material in data:
                for key, val in data[material].items():
                    if key in params[material]:
                        params[material][key] = val
        return jsonify({"success": True, "params": params})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/get_params")
def get_params():
    return jsonify(params)


@app.route("/reset_params", methods=["POST"])
def reset_params():
    global params
    params = json.loads(json.dumps(DEFAULT_PARAMS))
    return jsonify({"success": True, "params": params})


@app.route("/raw/<filename>")
def serve_raw(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/result/<filename>")
def serve_result(filename):
    return send_from_directory(RESULT_DIR, filename)


@app.route("/latest")
def latest():
    results = sorted(
        [f for f in os.listdir(RESULT_DIR) if f.startswith("result_")],
        reverse=True
    )[:20]
    return jsonify({"results": results})


if __name__ == "__main__":
    print("🔍 PiCam Vision server starting on http://localhost:5000")
    print("   Detecting: Copper · Aluminium · Iron bearing balls")
    app.run(host="127.0.0.1", port=5000, debug=False)