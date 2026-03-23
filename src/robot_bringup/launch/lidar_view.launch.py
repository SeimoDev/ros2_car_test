from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_dir = FindPackageShare("robot_bringup")
    serial_port = LaunchConfiguration("serial_port")
    frame_id = LaunchConfiguration("frame_id")
    rviz_config = PathJoinSubstitution(
        [
            EnvironmentVariable("HOME"),
            "ros2_car_test",
            "third_party",
            "sllidar_ros2",
            "rviz",
            "sllidar_ros2.rviz",
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB1"),
            DeclareLaunchArgument("frame_id", default_value="laser"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([bringup_dir, "launch", "lidar.launch.py"])
                ),
                launch_arguments={
                    "serial_port": serial_port,
                    "frame_id": frame_id,
                }.items(),
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="lidar_rviz",
                arguments=["-d", rviz_config],
                output="screen",
            ),
        ]
    )
