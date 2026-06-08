from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="realsense2_camera",
            executable="realsense2_camera_node",
            name="camera",
            namespace="camera",
            parameters=[{
                # D421: depth/infra, no RGB
                "enable_color": False,
                "enable_depth": True,
                "enable_infra1": True,
                "enable_infra2": True,

                # Not needed for stereo odometry
                "align_depth.enable": False,
                "pointcloud.enable": False,

                # Conservative stable profile
                "depth_module.depth_profile": "640x480x15",
                "depth_module.infra_profile": "640x480x15",

                "enable_sync": True,
                "clip_distance": 5.0,
            }],
            output="screen",
        ),
    ])
