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
                "enable_color": True,
                "enable_depth": True,
                "enable_infra1": False,
                "enable_infra2": False,
                "pointcloud.enable": False,
                "align_depth.enable": False,

                # Conservative. Increase when USB3 is available.
                "rgb_camera.color_profile": "424x240x6",
                "depth_module.depth_profile": "424x240x6",
            }],
            output="screen",
        ),
    ])
