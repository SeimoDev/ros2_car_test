from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="robot_driver",
            executable="test_arm",
            name="test_arm",
            output="screen",
        ),
    ])
