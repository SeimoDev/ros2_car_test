from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_port = LaunchConfiguration("serial_port")
    baudrate = LaunchConfiguration("baudrate")
    linear_field = LaunchConfiguration("linear_field")
    angular_field = LaunchConfiguration("angular_field")
    reverse_angular = LaunchConfiguration("reverse_angular")
    return LaunchDescription([
        DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("baudrate", default_value="115200"),
        DeclareLaunchArgument("linear_field", default_value="vy"),
        DeclareLaunchArgument("angular_field", default_value="wz"),
        DeclareLaunchArgument("reverse_angular", default_value="false"),
        Node(
            package="robot_driver",
            executable="test_motor",
            name="test_motor",
            parameters=[{
                "serial_port": serial_port,
                "baudrate": baudrate,
                "linear_field": linear_field,
                "angular_field": angular_field,
                "reverse_angular": reverse_angular,
            }],
            output="screen",
        ),
    ])
