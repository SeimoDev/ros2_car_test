from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_dir = FindPackageShare("robot_bringup")
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([bringup_dir, "launch", "lidar.launch.py"]))),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([bringup_dir, "launch", "motor.launch.py"]))),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(PathJoinSubstitution([bringup_dir, "launch", "arm.launch.py"]))),
    ])
