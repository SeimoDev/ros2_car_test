from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_dir = FindPackageShare("robot_bringup")
    motor_serial_port = LaunchConfiguration("motor_serial_port")
    lidar_serial_port = LaunchConfiguration("lidar_serial_port")
    lidar_frame_id = LaunchConfiguration("lidar_frame_id")

    return LaunchDescription([
        DeclareLaunchArgument("motor_serial_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("lidar_serial_port", default_value="/dev/ttyUSB1"),
        DeclareLaunchArgument("lidar_frame_id", default_value="laser"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([bringup_dir, "launch", "lidar.launch.py"])
            ),
            launch_arguments={
                "serial_port": lidar_serial_port,
                "frame_id": lidar_frame_id,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([bringup_dir, "launch", "motor.launch.py"])
            ),
            launch_arguments={"serial_port": motor_serial_port}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([bringup_dir, "launch", "arm.launch.py"])
            ),
        ),
    ])
