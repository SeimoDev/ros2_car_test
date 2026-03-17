import rclpy
from rclpy.node import Node


class TestArm(Node):
    def __init__(self):
        super().__init__("test_arm")
        self.get_logger().warn("Arm hardware and protocol are not configured yet. This is a placeholder aligned with 常用命令.md.")
        self.create_timer(5.0, self._tick)

    def _tick(self):
        self.get_logger().info("Provide arm controller model/protocol to enable real arm bringup.")


def main():
    rclpy.init()
    node = TestArm()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
