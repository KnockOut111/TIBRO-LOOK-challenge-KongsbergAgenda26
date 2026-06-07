from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=[
                "0.10", "0.0", "0.20",
                "0.0", "0.0", "0.0",
                "base_link",
                "camera_link",
            ],
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=[
                "0.05", "0.0", "0.10",
                "0.0", "0.0", "0.0",
                "base_link",
                "imu_front_link",
            ],
        ),

        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            arguments=[
                "-0.05", "0.0", "0.10",
                "0.0", "0.0", "0.0",
                "base_link",
                "imu_rear_link",
            ],
        ),
    ])
