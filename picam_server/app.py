import sys
import types
import os
import time
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

PHOTO_DIR = os.path.join(os.path.dirname(__file__), "photos")
os.makedirs(PHOTO_DIR, exist_ok=True)


def get_camera():
    """Set up the pykms/kms mock and return a Camera instance."""
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/capture", methods=["POST"])
def capture():
    try:
        timestamp = int(time.time() * 1000)
        filename = f"photo_{timestamp}.jpg"
        filepath = os.path.join(PHOTO_DIR, filename)

        cam = get_camera()
        cam.take_photo(filepath)

        return jsonify({"success": True, "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/photos/<filename>")
def serve_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/latest")
def latest():
    photos = sorted(
        [f for f in os.listdir(PHOTO_DIR) if f.endswith(".jpg")],
        reverse=True
    )
    return jsonify({"photos": photos[:20]})  # Return last 20


if __name__ == "__main__":
    print("📷 PiCam server starting...")
    print("   Open http://<raspberry-pi-ip>:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, debug=False)