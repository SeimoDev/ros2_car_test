from pathlib import Path

import rclpy
from rclpy.node import Node


class TestLidar(Node):
    def __init__(self):
        super().__init__("test_lidar")
        port = "/dev/ttyUSB1"
        self.get_logger().info(f"A1 lidar expected on {port}, exists={Path(port).exists()}")
        self.get_logger().info("Recommended command: ros2 launch robot_bringup lidar.launch.py")
        self.create_timer(5.0, self._tick)

    def _tick(self):
        self.get_logger().info("Check /scan after launching the lidar driver.")


def main():
    rclpy.init()
    node = TestLidar()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
