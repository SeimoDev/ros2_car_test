from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    display = LaunchConfiguration("display")
    xauthority = LaunchConfiguration("xauthority")
    viewer = LaunchConfiguration("viewer")

    return LaunchDescription(
        [
            DeclareLaunchArgument("display", default_value=":1"),
            DeclareLaunchArgument("xauthority", default_value="/home/nx/.Xauthority"),
            DeclareLaunchArgument(
                "viewer",
                default_value="/opt/OrbbecSDK_v1.10.8/Example/bin/depth_viewer",
            ),
            ExecuteProcess(
                cmd=[viewer],
                additional_env={
                    "DISPLAY": display,
                    "XAUTHORITY": xauthority,
                },
                output="screen",
            ),
        ]
    )
