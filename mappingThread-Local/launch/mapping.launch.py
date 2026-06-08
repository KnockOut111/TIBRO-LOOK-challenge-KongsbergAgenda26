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
            executable="stereo_odometry",
            name="stereo_odometry",
            output="screen",
            parameters=[{
                "frame_id": "camera_link",
                "odom_frame_id": "odom",
                "publish_tf": True,
                "approx_sync": True,
                "queue_size": 30,
                "topic_queue_size": 30,
                "sync_queue_size": 10,
            }],
            remappings=[
                ("left/image_rect", "/camera/camera/infra1/image_rect_raw"),
                ("right/image_rect", "/camera/camera/infra2/image_rect_raw"),
                ("left/camera_info", "/camera/camera/infra1/camera_info"),
                ("right/camera_info", "/camera/camera/infra2/camera_info"),
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
