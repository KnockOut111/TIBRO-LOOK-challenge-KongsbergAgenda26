from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    pkg_share = FindPackageShare("mapping_thread_local")

    realsense_launch = PathJoinSubstitution([
        pkg_share, "launch", "realsense_minimal.launch.py"
    ])

    static_tf_launch = PathJoinSubstitution([
        pkg_share, "launch", "static_tf.launch.py"
    ])

    ekf_config = PathJoinSubstitution([
        pkg_share, "config", "ekf.yaml"
    ])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(realsense_launch),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(static_tf_launch),
        ),

        Node(
            package="rtabmap_odom",
            executable="rgbd_odometry",
            name="rgbd_odometry",
            output="screen",
            parameters=[{
                "frame_id": "base_link",
                "odom_frame_id": "rtabmap_odom",
                "publish_tf": False,
                "approx_sync": True,
            }],
            remappings=[
                ("rgb/image", "/camera/camera/color/image_raw"),
                ("depth/image", "/camera/camera/depth/image_rect_raw"),
                ("rgb/camera_info", "/camera/camera/color/camera_info"),
                ("odom", "/rtabmap/odom"),
            ],
        ),

        Node(
            package="robot_localization",
            executable="ekf_node",
            name="ekf_filter_node",
            output="screen",
            parameters=[ekf_config],
        ),
    ])
