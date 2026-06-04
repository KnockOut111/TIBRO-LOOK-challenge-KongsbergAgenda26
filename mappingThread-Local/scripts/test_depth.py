import pyrealsense2 as rs

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

pipeline.start(config)

print("Streaming depth...")

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth = frames.get_depth_frame()

        if not depth:
            continue

        distance = depth.get_distance(320, 240)
        print(f"Center distance: {distance:.3f} meters")

except KeyboardInterrupt:
    pass

pipeline.stop()
