"""
RealSense D421 Room Mapper — Raspberry Pi 5 edition
Snapshot mode: captures one depth frame every 5 seconds.
Uses plain Flask HTTP polling — no WebSocket, no eventlet.

Noise rejection:
  - Median over N_FRAMES frames per pixel
  - Min distance gate (ignore < MIN_DIST, near-field noise)
  - Neighbour agreement filter: a sample is kept only if at least
    MIN_NEIGHBOURS neighbouring pixels read a similar distance
"""

import math, time, random, json, argparse
from flask import Flask, jsonify, render_template

try:
    import pyrealsense2 as rs
    import numpy as np
    RS_AVAILABLE = True
except ImportError:
    RS_AVAILABLE = False
    print("[WARN] pyrealsense2 not found — demo mode.")

app = Flask(__name__)

# ── Shared snapshot state ─────────────────────────────────────────────────────
latest_scan = {"rays": [], "center": 0, "fov": 87, "range": 6.0, "source": "waiting", "ts": 0}

FOV_H          = 87.0
FOV_V          = 58.0
MAX_RANGE      = 6.0
MIN_DIST       = 0.4    # metres — discard closer than this (near-field noise)
INTERVAL       = 5      # seconds between snapshots
COL_STEP       = 16     # sample every Nth column
ROW_STEP       = 16     # sample every Nth row
N_FRAMES       = 5      # frames to median-stack per snapshot
AGREE_RADIUS   = 1      # neighbour check radius in grid steps
AGREE_TOL      = 0.15   # metres — neighbours must be within this
MIN_NEIGHBOURS = 2      # minimum agreeing neighbours to keep a point

# ── Camera snapshot ───────────────────────────────────────────────────────────
def capture_snapshot():
    global latest_scan
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    try:
        pipeline.start(cfg)

        # Warm-up: discard first 15 frames
        for _ in range(15):
            pipeline.wait_for_frames()

        w, h = 640, 480

        # ── Step 1: collect N_FRAMES and median-stack ──────────────────────
        # depth_stack shape: (N_FRAMES, sampled_rows, sampled_cols)
        cols = list(range(0, w, COL_STEP))
        rows = list(range(0, h, ROW_STEP))
        stack = np.zeros((N_FRAMES, len(rows), len(cols)), dtype=np.float32)

        for fi in range(N_FRAMES):
            frames = pipeline.wait_for_frames()
            depth  = frames.get_depth_frame()
            if not depth:
                continue
            for ri, cy in enumerate(rows):
                for ci, cx in enumerate(cols):
                    stack[fi, ri, ci] = depth.get_distance(cx, cy)

        # Median across frames → (rows, cols) array
        med = np.median(stack, axis=0)   # shape (len(rows), len(cols))

        # ── Step 2: build raw ray list with distance gate ──────────────────
        # raw_grid[ri][ci] = horizontal distance or None
        raw = {}
        for ri, cy in enumerate(rows):
            v_angle = ((cy / (h - 1)) - 0.5) * FOV_V
            cos_v   = math.cos(math.radians(v_angle))
            for ci, cx in enumerate(cols):
                d = float(med[ri, ci])
                if MIN_DIST < d < MAX_RANGE:
                    raw[(ri, ci)] = d * cos_v   # project to horizontal plane
                else:
                    raw[(ri, ci)] = None

        # ── Step 3: neighbour-agreement filter ────────────────────────────
        rays = []
        for ri, cy in enumerate(rows):
            h_angle_base = lambda cx: ((cx / (w - 1)) - 0.5) * FOV_H
            for ci, cx in enumerate(cols):
                d = raw[(ri, ci)]
                if d is None:
                    continue
                # Count neighbours with a similar reading
                agree = 0
                for dr in range(-AGREE_RADIUS, AGREE_RADIUS + 1):
                    for dc in range(-AGREE_RADIUS, AGREE_RADIUS + 1):
                        if dr == 0 and dc == 0:
                            continue
                        nd = raw.get((ri + dr, ci + dc))
                        if nd is not None and abs(nd - d) < AGREE_TOL:
                            agree += 1
                if agree >= MIN_NEIGHBOURS:
                    h_angle = ((cx / (w - 1)) - 0.5) * FOV_H
                    rays.append({"a": round(h_angle, 1), "d": round(d, 3)})

        # Centre distance: median of a 3×3 patch around the middle
        mid_r, mid_c = len(rows) // 2, len(cols) // 2
        patch = []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                v = raw.get((mid_r + dr, mid_c + dc))
                if v: patch.append(v)
        center = round(float(np.median(patch)), 3) if patch else 0.0

        latest_scan = {"rays": rays, "center": center, "fov": FOV_H,
                       "range": MAX_RANGE, "source": "camera", "ts": time.time()}
        print(f"[SNAP] {len(rays)} rays (after filter), center={center:.2f}m")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        pipeline.stop()

# ── Demo snapshot ─────────────────────────────────────────────────────────────
_demo_tick = 0
def demo_snapshot():
    global latest_scan, _demo_tick
    rays = []
    for a_int in range(-int(FOV_H / 2), int(FOV_H / 2) + 1, 3):
        a = float(a_int)
        rad = math.radians(a)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        ts = []
        if cos_a > 0.001: ts.append(3.0 / cos_a)
        if sin_a > 0.001: ts.append(2.5 / sin_a)
        if sin_a < -0.001: ts.append(2.5 / -sin_a)
        wall_d = min(ts) if ts else MAX_RANGE
        # Moving obstacle
        obj_a = 30 * math.sin(_demo_tick * 0.4)
        if abs(a - obj_a) < 9:
            wall_d = min(wall_d, 1.6 + 0.2 * math.sin(_demo_tick))
        d = max(0.1, wall_d + random.gauss(0, 0.01))
        rays.append({"a": a, "d": round(d, 3)})
    center = next((r["d"] for r in rays if r["a"] == 0.0), 0)
    latest_scan = {"rays": rays, "center": round(center, 3), "fov": FOV_H,
                   "range": MAX_RANGE, "source": "demo", "ts": time.time()}
    _demo_tick += 1
    print(f"[DEMO] {len(rays)} rays, center={center:.2f}m")

# ── Background snapshot loop ──────────────────────────────────────────────────
import threading

def snapshot_loop():
    while True:
        if RS_AVAILABLE:
            capture_snapshot()
        else:
            demo_snapshot()
        time.sleep(INTERVAL)

t = threading.Thread(target=snapshot_loop, daemon=True)
t.start()

# ── Flask routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan")
def scan():
    return jsonify(latest_scan)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    if args.demo:
        globals()["RS_AVAILABLE"] = False
    INTERVAL = args.interval
    print(f"Open http://<pi-ip>:{args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)