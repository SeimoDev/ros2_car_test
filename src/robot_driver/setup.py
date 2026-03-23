from setuptools import setup

package_name = "robot_driver"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="nx",
    maintainer_email="nx@example.com",
    description="Hardware test helpers aligned with 常用命令.md",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "test_arm = robot_driver.test_arm:main",
            "test_motor = robot_driver.test_motor:main",
            "test_lidar = robot_driver.test_lidar:main",
            "test_camera = robot_driver.test_camera:main",
            "drive_state_publisher = robot_driver.drive_state_publisher:main",
            "heading_pid = robot_driver.heading_pid:main",
            "safety_stop = robot_driver.safety_stop:main",
        ],
    },
)
