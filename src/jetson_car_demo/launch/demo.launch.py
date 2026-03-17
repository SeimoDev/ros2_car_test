from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    image_topic = LaunchConfiguration("image_topic")
    start_keyboard = LaunchConfiguration("start_keyboard")

    return LaunchDescription([
        DeclareLaunchArgument("image_topic", default_value="/image_raw"),
        DeclareLaunchArgument("start_keyboard", default_value="false"),
        LogInfo(msg="camera_viewer started. Run keyboard_drive in an interactive terminal if you want keyboard control."),
        LogInfo(
            condition=IfCondition(start_keyboard),
            msg="start_keyboard:=true was requested, but keyboard_drive still needs an interactive TTY terminal.",
        ),
        Node(
            package="jetson_car_demo",
            executable="camera_viewer",
            name="camera_viewer",
            parameters=[{"image_topic": image_topic}],
            output="screen",
        ),
    ])
