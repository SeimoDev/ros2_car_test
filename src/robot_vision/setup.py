from setuptools import setup

package_name = "robot_vision"

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
    description="Vision utilities for manual ROI tracking and target following.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "roi_follower = robot_vision.roi_follower:main",
        ],
    },
)
