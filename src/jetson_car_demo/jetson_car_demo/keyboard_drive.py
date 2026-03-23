import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

HELP = """Keyboard drive demo
-------------------
w/s : forward/back
j/l : turn left/right
i/k : accelerate/decelerate
x   : stop
q   : quit
"""


class KeyboardDrive(Node):
    def __init__(self):
        super().__init__("keyboard_drive")
        self.publisher = self.create_publisher(Twist, "cmd_vel", 10)
        self.linear_step = float(self.declare_parameter("linear_step", 2.0).value)
        self.angular_step = float(self.declare_parameter("angular_step", 6.0).value)
        self.max_linear = float(self.declare_parameter("max_linear", 10.0).value)
        self.max_angular = float(self.declare_parameter("max_angular", 20.0).value)
        self.linear = 0.0
        self.angular = 0.0
        self.get_logger().info(HELP)

    def publish_twist(self):
        msg = Twist()
        msg.linear.x = self.linear
        msg.angular.z = self.angular
        self.publisher.publish(msg)
        self.get_logger().info(
            f"cmd_vel -> linear.x={msg.linear.x:.2f}, angular.z={msg.angular.z:.2f}"
        )

    @staticmethod
    def clamp(value, limit):
        return max(min(value, limit), -limit)

    @staticmethod
    def decelerate_towards_zero(value, step):
        if value > 0.0:
            return max(0.0, value - step)
        if value < 0.0:
            return min(0.0, value + step)
        return 0.0

    def handle_key(self, key):
        if key == "w":
            self.linear = self.clamp(self.linear + self.linear_step, self.max_linear)
        elif key == "s":
            self.linear = self.clamp(self.linear - self.linear_step, self.max_linear)
        elif key == "j":
            self.angular = self.clamp(self.angular + self.angular_step, self.max_angular)
        elif key == "l":
            self.angular = self.clamp(self.angular - self.angular_step, self.max_angular)
        elif key == "i":
            direction = 1.0 if self.linear >= 0.0 else -1.0
            self.linear = self.clamp(self.linear + direction * self.linear_step, self.max_linear)
        elif key == "k":
            self.linear = self.decelerate_towards_zero(self.linear, self.linear_step)
        elif key == "x":
            self.linear = 0.0
            self.angular = 0.0
        else:
            return key == "q"
        self.publish_twist()
        return False


def read_key(settings):
    tty.setraw(sys.stdin.fileno())
    try:
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            return sys.stdin.read(1)
        return ""
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = KeyboardDrive()
    try:
        while rclpy.ok():
            key = read_key(settings)
            if not key:
                continue
            if node.handle_key(key):
                break
    finally:
        node.linear = 0.0
        node.angular = 0.0
        node.publish_twist()
        node.destroy_node()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)


if __name__ == "__main__":
    main()
