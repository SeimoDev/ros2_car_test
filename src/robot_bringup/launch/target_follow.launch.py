from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    video_device = LaunchConfiguration("video_device")
    output_topic = LaunchConfiguration("output_topic")
    display = LaunchConfiguration("display")
    xauthority = LaunchConfiguration("xauthority")
    motion_enabled = LaunchConfiguration("motion_enabled")

    return LaunchDescription(
        [
            DeclareLaunchArgument("video_device", default_value="/dev/video2"),
            DeclareLaunchArgument("output_topic", default_value="/cmd_vel"),
            DeclareLaunchArgument("display", default_value=":1"),
            DeclareLaunchArgument("xauthority", default_value="/home/nx/.Xauthority"),
            DeclareLaunchArgument("motion_enabled", default_value="false"),
            Node(
                package="robot_vision",
                executable="roi_follower",
                name="roi_follower",
                parameters=[
                    {
                        "video_device": video_device,
                        "output_topic": output_topic,
                        "motion_enabled": motion_enabled,
                    }
                ],
                additional_env={
                    "DISPLAY": display,
                    "XAUTHORITY": xauthority,
                },
                output="screen",
            ),
        ]
    )
