# PiCam Web Server

A minimal local web interface for your Raspberry Pi camera.

## Setup

```bash
# Install dependencies
pip install flask picamzero --break-system-packages

# Run the server
python app.py
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

- Click **SHOOT** (or press **Space**) to take a photo
- Photos appear instantly in the viewer
- Thumbnail strip at the bottom shows all captured photos
- Photos are saved in the `photos/` folder next to `app.py`

## Notes

- The server binds to `0.0.0.0:5000` so it's reachable from any device on your local network
- Photos persist between restarts and are reloaded automatically on page open
- The pykms/kms mock is included so picamzero works without a display server