from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    motor_serial_port = LaunchConfiguration("motor_serial_port")
    lidar_serial_port = LaunchConfiguration("lidar_serial_port")
    bringup_dir = FindPackageShare("robot_bringup")
    return LaunchDescription(
        [
            DeclareLaunchArgument("motor_serial_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("lidar_serial_port", default_value="/dev/ttyUSB1"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([bringup_dir, "launch", "lidar.launch.py"])
                ),
                launch_arguments={"serial_port": lidar_serial_port}.items(),
            ),
            Node(
                package="robot_driver",
                executable="test_motor",
                name="test_motor",
                parameters=[
                    {
                        "serial_port": motor_serial_port,
                        "linear_field": "vy",
                        "angular_field": "wz",
                    }
                ],
                output="screen",
            ),
            Node(
                package="robot_driver",
                executable="drive_state_publisher",
                name="drive_state_publisher",
                parameters=[{"command_topic": "/cmd_vel"}],
                output="screen",
            ),
            Node(
                package="robot_driver",
                executable="safety_stop",
                name="safety_stop",
                parameters=[
                    {
                        "input_topic": "/cmd_vel_raw",
                        "output_topic": "/cmd_vel",
                        "scan_topic": "/scan",
                        "safety_distance": 0.5,
                    }
                ],
                output="screen",
            ),
        ]
    )
