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
    max_linear = LaunchConfiguration("max_linear")
    max_angular = LaunchConfiguration("max_angular")
    return LaunchDescription([
        DeclareLaunchArgument("serial_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("baudrate", default_value="115200"),
        DeclareLaunchArgument("linear_field", default_value="vy"),
        DeclareLaunchArgument("angular_field", default_value="wz"),
        DeclareLaunchArgument("reverse_angular", default_value="false"),
        DeclareLaunchArgument("max_linear", default_value="7.0"),
        DeclareLaunchArgument("max_angular", default_value="24.0"),
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
                "max_linear": max_linear,
                "max_angular": max_angular,
            }],
            output="screen",
        ),
    ])
