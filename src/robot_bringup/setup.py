from setuptools import setup

package_name = "robot_bringup"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            [
                "launch/lidar.launch.py",
                "launch/motor.launch.py",
                "launch/arm.launch.py",
                "launch/robot_bringup.launch.py",
                "launch/experiment1_odom.launch.py",
                "launch/experiment2_sensors.launch.py",
                "launch/experiment3_speed_control.launch.py",
                "launch/experiment4_demo.launch.py",
                "launch/project2_speed_control.launch.py",
                "launch/project2_demo.launch.py",
                "launch/lidar_view.launch.py",
                "launch/camera_view.launch.py",
                "launch/depth_camera_view.launch.py",
                "launch/target_follow.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="nx",
    maintainer_email="nx@example.com",
    description="Bringup package aligned with 常用命令.md",
    license="Apache-2.0",
)
