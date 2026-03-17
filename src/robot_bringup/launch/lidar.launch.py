from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    serial_port = LaunchConfiguration("serial_port")
    frame_id = LaunchConfiguration("frame_id")
    return LaunchDescription([
        DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB1"),
        DeclareLaunchArgument("frame_id", default_value="laser"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare("sllidar_ros2"),
                    "launch",
                    "sllidar_a1_launch.py",
                ])
            ),
            launch_arguments={
                "serial_port": serial_port,
                "frame_id": frame_id,
            }.items(),
        ),
    ])
