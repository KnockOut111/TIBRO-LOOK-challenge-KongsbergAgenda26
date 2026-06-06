# PiCam Web Server

A minimal local web interface for a Raspberry Pi camera.

The current rover flow is:

1. `app_detect.py` runs the web server and shows the latest frame.
2. `picam2_node.py` runs as the ROS camera node.
3. The ROS node continuously captures frames, optionally runs YOLOv8, publishes detections on `/camera/detections`, and uploads the latest frame to the web server.

This keeps the Pi camera useful even if object detection is disabled or the model is missing.

## Setup

```bash
# Install dependencies
pip install flask picamzero --break-system-packages

# Run the detection/live-frame web server
python app_detect.py

# In another terminal, run the ROS camera node
python picam2_node.py
```

## Access

Find your Pi's IP address:
```bash
hostname -I
```

Then open in your PC browser:
```
http://<raspberry-pi-ip>:5000
```

## Usage

- Keep `picam2_node.py` running to stream latest frames into the viewer
- Click **SHOOT** (or press **Space**) to take a manual photo
- Photos and live frames appear instantly in the viewer
- Thumbnail strip at the bottom shows all captured photos
- Photos are saved in the `photos/` folder next to `app.py`

## ROS Node Parameters

```bash
python picam2_node.py --ros-args \
  -p server_url:=http://<raspberry-pi-ip>:5000/api/upload \
  -p capture_rate_hz:=2.0 \
  -p confidence_threshold:=0.4
```

- `server_url`: where frames are uploaded for the web UI
- `capture_rate_hz`: frame upload/detection rate
- `confidence_threshold`: YOLO detection confidence threshold

## Notes

- The server binds to `0.0.0.0:5000` so it's reachable from any device on your local network
- Photos persist between restarts and are reloaded automatically on page open
- The pykms/kms mock is included so picamzero works without a display server
