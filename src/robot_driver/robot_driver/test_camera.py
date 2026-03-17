from pathlib import Path

import rclpy
from rclpy.node import Node


class TestCamera(Node):
    def __init__(self):
        super().__init__("test_camera")
        video_nodes = [str(p) for p in sorted(Path("/dev").glob("video*"))]
        media_nodes = [str(p) for p in sorted(Path("/dev").glob("media*"))]
        self.get_logger().info(f"video devices: {video_nodes or [none]}")
        self.get_logger().info(f"media devices: {media_nodes or [none]}")
        self.get_logger().info("If a UVC camera appears as /dev/video0, try: ros2 run v4l2_camera v4l2_camera_node")
        self.create_timer(5.0, self._tick)

    def _tick(self):
        self.get_logger().info("Unknown depth camera still needs brand/model identification for a dedicated ROS 2 driver.")


def main():
    rclpy.init()
    node = TestCamera()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
