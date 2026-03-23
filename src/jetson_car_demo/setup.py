from setuptools import setup

package_name = 'jetson_car_demo'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md']),
        ('share/' + package_name + '/launch', ['launch/demo.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nx',
    maintainer_email='nx@example.com',
    description='Jetson Xavier NX demo for keyboard driving and camera viewing.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'keyboard_drive = jetson_car_demo.keyboard_drive:main',
            'teleop_keyboard = jetson_car_demo.teleop_keyboard:main',
            'camera_viewer = jetson_car_demo.camera_viewer:main',
        ],
    },
)
