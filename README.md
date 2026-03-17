# ros2_car_test

ROS 2 Foxy workspace for the Jetson-based car platform.

This repository contains:

- `src/jetson_car_demo`: keyboard drive and camera viewer demo
- `src/robot_bringup`: launch files for lidar, motor, arm, and combined bringup
- `src/robot_driver`: serial and hardware test nodes
- `src/robot_arm`, `src/robot_navigation`, `src/robot_vision`, `src/robot_voice`, `src/robot_experiment`: package skeletons aligned with the workspace layout
- `third_party/sllidar_ros2`: SLLidar A1 ROS 2 driver source used on the Jetson
- `docs/常用命令.md`: reference command notes used during setup

## Workspace layout

```text
ros2_car_test/
├── src/
├── third_party/
└── docs/
```

## Build

```bash
source /opt/ros/foxy/setup.bash
cd ~/ros2_car_test
colcon build --symlink-install
source install/setup.bash
```

## Runtime

Motor bridge:

```bash
ros2 launch robot_bringup motor.launch.py
```

LiDAR:

```bash
ros2 launch robot_bringup lidar.launch.py serial_port:=/dev/ttyUSB2
```

Keyboard drive:

```bash
ros2 run jetson_car_demo keyboard_drive
```

Camera viewer:

```bash
ros2 launch jetson_car_demo demo.launch.py
```

## Notes

- The STM32 motor bridge currently uses an inferred serial protocol in `src/robot_driver/robot_driver/test_motor.py`.
- The validated default motor mapping is `linear_field=vy` and `angular_field=wz`.
- The LiDAR on the target Jetson was validated on `/dev/ttyUSB2`.
