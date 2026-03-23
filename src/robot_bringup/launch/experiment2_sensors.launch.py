from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    motor_serial_port = LaunchConfiguration("motor_serial_port")
    return LaunchDescription(
        [
            DeclareLaunchArgument("motor_serial_port", default_value="/dev/ttyUSB0"),
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
        ]
    )
