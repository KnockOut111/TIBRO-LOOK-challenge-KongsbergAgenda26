import sys
import types
import os
import time
import json
import shutil
import numpy as np
import cv2
from flask import Flask, render_template, jsonify, send_from_directory, request

app = Flask(__name__, template_folder="templates")

PHOTO_DIR = os.path.join(os.path.dirname(__file__), "photos")
DETECT_DIR = os.path.join(os.path.dirname(__file__), "photos_detected")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "yolov8n.onnx")
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(DETECT_DIR, exist_ok=True)
LATEST_RAW = "latest_raw.jpg"
LATEST_DETECTED = "latest_detected.jpg"
latest_frame = {
    "raw": None,
    "detected": None,
    "detections": [],
    "timestamp": None,
    "source": None,
}

# COCO class names (80 classes YOLOv8 was trained on)
COCO_CLASSES = [
    "person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
    "traffic light","fire hydrant","stop sign","parking meter","bench","bird","cat",
    "dog","horse","sheep","cow","elephant","bear","zebra","giraffe","backpack",
    "umbrella","handbag","tie","suitcase","frisbee","skis","snowboard","sports ball",
    "kite","baseball bat","baseball glove","skateboard","surfboard","tennis racket",
    "bottle","wine glass","cup","fork","knife","spoon","bowl","banana","apple",
    "sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake","chair",
    "couch","potted plant","bed","dining table","toilet","tv","laptop","mouse",
    "remote","keyboard","cell phone","microwave","oven","toaster","sink","refrigerator",
    "book","clock","vase","scissors","teddy bear","hair drier","toothbrush"
]

# Generate a distinct color per class
def class_color(cls_id):
    np.random.seed(cls_id * 7 + 13)
    return tuple(int(c) for c in np.random.randint(80, 255, 3))


def label_color(label):
    seed = sum((i + 1) * ord(c) for i, c in enumerate(label))
    np.random.seed(seed)
    return tuple(int(c) for c in np.random.randint(80, 255, 3))

# Load ONNX model once at startup
ort_session = None
def load_model():
    global ort_session
    if not os.path.exists(MODEL_PATH):
        print(f"⚠️  Model not found at {MODEL_PATH}")
        print("   Download yolov8n.onnx and place it next to app_detect.py")
        return False
    try:
        import onnxruntime as ort
        ort_session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
        print("✅ YOLOv8n ONNX model loaded")
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False


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


def run_detection(image_path, out_path, conf_threshold=0.4, iou_threshold=0.45):
    """Run YOLOv8 ONNX inference and draw bounding boxes. Returns list of detections."""
    if ort_session is None:
        raise RuntimeError("Model not loaded")

    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Could not read image: {image_path}")

    orig_h, orig_w = img.shape[:2]

    # Preprocess: resize to 640x640, normalize
    input_size = 640
    img_resized = cv2.resize(img, (input_size, input_size))
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_norm = img_rgb.astype(np.float32) / 255.0
    img_input = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...]  # NCHW

    # Inference
    input_name = ort_session.get_inputs()[0].name
    outputs = ort_session.run(None, {input_name: img_input})
    predictions = outputs[0][0]  # shape: (84, 8400)

    # Decode: YOLOv8 output is (cx, cy, w, h, class_scores...)
    predictions = predictions.T  # (8400, 84)
    boxes_xywh = predictions[:, :4]
    class_scores = predictions[:, 4:]

    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(len(class_ids)), class_ids]

    # Filter by confidence
    mask = confidences >= conf_threshold
    boxes_xywh = boxes_xywh[mask]
    confidences = confidences[mask]
    class_ids = class_ids[mask]

    # Convert cx,cy,w,h -> x1,y1,x2,y2 (normalized 0-640 space -> original image space)
    scale_x = orig_w / input_size
    scale_y = orig_h / input_size

    boxes_xyxy = []
    for box in boxes_xywh:
        cx, cy, w, h = box
        x1 = int((cx - w / 2) * scale_x)
        y1 = int((cy - h / 2) * scale_y)
        x2 = int((cx + w / 2) * scale_x)
        y2 = int((cy + h / 2) * scale_y)
        boxes_xyxy.append([x1, y1, x2, y2])

    # NMS
    detections = []
    if boxes_xyxy:
        boxes_for_nms = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes_xyxy]
        indices = cv2.dnn.NMSBoxes(
            boxes_for_nms,
            confidences.tolist(),
            conf_threshold,
            iou_threshold
        )
        if len(indices) > 0:
            indices = indices.flatten()
            for i in indices:
                x1, y1, x2, y2 = boxes_xyxy[i]
                cls_id = int(class_ids[i])
                conf = float(confidences[i])
                label = COCO_CLASSES[cls_id] if cls_id < len(COCO_CLASSES) else f"cls{cls_id}"
                color = class_color(cls_id)

                # Draw box
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                # Draw label background
                text = f"{label} {conf:.0%}"
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                label_y = max(y1, th + 6)
                cv2.rectangle(img, (x1, label_y - th - 6), (x1 + tw + 6, label_y), color, -1)
                cv2.putText(img, text, (x1 + 3, label_y - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)

                detections.append({"label": label, "confidence": round(conf, 3),
                                   "box": [x1, y1, x2, y2]})

    cv2.imwrite(out_path, img)
    return detections


def draw_detections(img, detections):
    result_img = img.copy()
    for det in detections:
        box = det.get("box")
        if not box or len(box) != 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in box]
        label = str(det.get("label", "object"))
        confidence = float(det.get("confidence", 0.0))
        color = label_color(label)

        cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
        text = f"{label} {confidence:.0%}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        label_y = max(y1, th + 6)
        cv2.rectangle(
            result_img,
            (x1, label_y - th - 6),
            (x1 + tw + 6, label_y),
            color,
            -1,
        )
        cv2.putText(
            result_img,
            text,
            (x1 + 3, label_y - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    return result_img


def remember_latest(raw_filename, detected_filename, detections, source):
    latest_frame["raw"] = raw_filename
    latest_frame["detected"] = detected_filename
    latest_frame["detections"] = detections
    latest_frame["timestamp"] = time.time()
    latest_frame["source"] = source


@app.route("/")
def index():
    return render_template("index_detect.html")


@app.route("/capture", methods=["POST"])
def capture():
    try:
        timestamp = int(time.time() * 1000)
        raw_filename = f"photo_{timestamp}.jpg"
        det_filename = f"detected_{timestamp}.jpg"
        raw_path = os.path.join(PHOTO_DIR, raw_filename)
        det_path = os.path.join(DETECT_DIR, det_filename)

        # Take photo
        cam = get_camera()
        cam.take_photo(raw_path)

        # Run detection
        t0 = time.time()
        detections = run_detection(raw_path, det_path)
        elapsed = round(time.time() - t0, 2)
        shutil.copyfile(raw_path, os.path.join(PHOTO_DIR, LATEST_RAW))
        shutil.copyfile(det_path, os.path.join(DETECT_DIR, LATEST_DETECTED))
        remember_latest(raw_filename, det_filename, detections, "manual")

        return jsonify({
            "success": True,
            "raw": raw_filename,
            "detected": det_filename,
            "detections": detections,
            "inference_ms": elapsed
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/photos/<filename>")
def serve_raw(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/detected/<filename>")
def serve_detected(filename):
    return send_from_directory(DETECT_DIR, filename)


@app.route("/api/upload", methods=["POST"])
def upload():
    try:
        image = request.files.get("image")
        if image is None:
            return jsonify({"success": False, "error": "Missing image"}), 400

        detections_raw = request.form.get("detections", "[]")
        try:
            detections = json.loads(detections_raw)
        except json.JSONDecodeError:
            detections = []

        timestamp = int(time.time() * 1000)
        raw_filename = f"upload_{timestamp}.jpg"
        detected_filename = f"upload_detected_{timestamp}.jpg"
        raw_path = os.path.join(PHOTO_DIR, raw_filename)
        detected_path = os.path.join(DETECT_DIR, detected_filename)

        image.save(raw_path)
        img = cv2.imread(raw_path)
        if img is None:
            return jsonify({"success": False, "error": "Could not decode image"}), 400

        detected_img = draw_detections(img, detections)
        cv2.imwrite(detected_path, detected_img)
        cv2.imwrite(os.path.join(PHOTO_DIR, LATEST_RAW), img)
        cv2.imwrite(os.path.join(DETECT_DIR, LATEST_DETECTED), detected_img)

        remember_latest(raw_filename, detected_filename, detections, "ros")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/latest")
def api_latest():
    return jsonify({
        "success": latest_frame["raw"] is not None,
        **latest_frame,
    })


@app.route("/latest_raw.jpg")
def latest_raw_image():
    return send_from_directory(PHOTO_DIR, LATEST_RAW)


@app.route("/latest_detected.jpg")
def latest_detected_image():
    return send_from_directory(DETECT_DIR, LATEST_DETECTED)


@app.route("/latest")
def latest():
    det_files = sorted(
        [f for f in os.listdir(DETECT_DIR) if f.endswith(".jpg")],
        reverse=True
    )[:20]
    return jsonify({"photos": det_files})


@app.route("/model_status")
def model_status():
    return jsonify({"loaded": ort_session is not None})


if __name__ == "__main__":
    load_model()
    print("📷 PiCam DETECT server starting on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
