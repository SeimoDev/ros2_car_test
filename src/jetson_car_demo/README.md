# Jetson Car Demo

这个包提供两个最小 ROS 2 示例节点：

- `keyboard_drive`：通过键盘发布 `geometry_msgs/msg/Twist` 到小车速度话题。
- `camera_viewer`：订阅 `sensor_msgs/msg/Image` 并用 OpenCV 弹窗显示摄像头画面。

## 默认话题

- 速度话题：`/cmd_vel`
- 图像话题：`/image_raw`

## 编译

```bash
cd ~/Desktop/ros2_ws
source /opt/ros/foxy/setup.bash
colcon build --packages-select jetson_car_demo
source install/setup.bash
```

## 运行方式

### 终端 1：启动摄像头查看

```bash
cd ~/Desktop/ros2_ws
source /opt/ros/foxy/setup.bash
source install/setup.bash
ros2 launch jetson_car_demo demo.launch.py
```

如果你的图像话题不同：

```bash
ros2 launch jetson_car_demo demo.launch.py image_topic:=/camera/image_raw
```

### 终端 2：启动键盘控制

`keyboard_drive` 必须运行在交互式终端里，不能直接作为 `ros2 launch` 里的普通后台进程启动。

```bash
cd ~/Desktop/ros2_ws
source /opt/ros/foxy/setup.bash
source install/setup.bash
ros2 run jetson_car_demo keyboard_drive
```

如果你的底盘实际订阅话题不是 `/cmd_vel`，用 remap：

```bash
ros2 run jetson_car_demo keyboard_drive --ros-args -r cmd_vel:=/car/cmd_vel
```

## 键盘操作

- `w`：前进
- `s`：后退
- `j`：左转
- `l`：右转
- `x`：停车
- `q`：退出

每按一次会更新一次速度并立即发布。

## 单独运行摄像头查看

```bash
ros2 run jetson_car_demo camera_viewer --ros-args -p image_topic:=/image_raw
```

## 调试命令

```bash
ros2 topic list
ros2 topic echo /cmd_vel
ros2 topic hz /image_raw
```

## 注意事项

- `camera_viewer` 当前支持 `bgr8`、`rgb8`、`mono8` 三种图像编码。
- 该示例不依赖 `cv_bridge`，适合当前 Jetson OpenCV 环境。
- 如果通过纯 SSH 终端运行图像窗口，需要远端桌面会话和显示权限。
- `keyboard_drive` 依赖 TTY 键盘输入，因此请在独立交互终端中运行。
