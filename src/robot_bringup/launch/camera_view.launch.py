from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    video_device = LaunchConfiguration("video_device")
    image_topic = LaunchConfiguration("image_topic")
    display = LaunchConfiguration("display")
    return LaunchDescription(
        [
            DeclareLaunchArgument("video_device", default_value="/dev/video0"),
            DeclareLaunchArgument("image_topic", default_value="/image_raw"),
            DeclareLaunchArgument("display", default_value=":1"),
            Node(
                package="v4l2_camera",
                executable="v4l2_camera_node",
                name="v4l2_camera",
                parameters=[
                    {
                        "video_device": video_device,
                        "image_size": [640, 480],
                    }
                ],
                remappings=[("/image_raw", image_topic), ("/camera_info", "/camera_info")],
                output="screen",
            ),
            Node(
                package="jetson_car_demo",
                executable="camera_viewer",
                name="camera_viewer",
                parameters=[{"image_topic": image_topic}],
                additional_env={"DISPLAY": display},
                output="screen",
            ),
        ]
    )
