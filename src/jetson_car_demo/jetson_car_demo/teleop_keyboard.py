import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

HELP = """
Control Your Robot
------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

q/z : increase/decrease all speeds by 10%
w/x : increase/decrease linear speed by 10%
e/c : increase/decrease angular speed by 10%
k   : stop
CTRL-C to quit
"""

MOVE_BINDINGS = {
    "i": (1.0, 0.0),
    ",": (-1.0, 0.0),
    "j": (0.0, 1.0),
    "l": (0.0, -1.0),
    "u": (1.0, 1.0),
    "o": (1.0, -1.0),
    "m": (-1.0, -1.0),
    ".": (-1.0, 1.0),
}

SPEED_BINDINGS = {
    "q": (1.1, 1.1),
    "z": (0.9, 0.9),
    "w": (1.1, 1.0),
    "x": (0.9, 1.0),
    "e": (1.0, 1.1),
    "c": (1.0, 0.9),
}


class TeleopKeyboard(Node):
    def __init__(self):
        super().__init__("teleop_keyboard")
        output_topic = str(self.declare_parameter("output_topic", "/cmd_vel_raw").value)
        self.linear_speed = float(self.declare_parameter("linear_speed", 2.0).value)
        self.angular_speed = float(self.declare_parameter("angular_speed", 6.0).value)
        self.publisher = self.create_publisher(Twist, output_topic, 10)
        self.settings = termios.tcgetattr(sys.stdin)
        self.get_logger().info(HELP)
        self.get_logger().info(
            f"Publishing keyboard commands to {output_topic} "
            f"(linear={self.linear_speed:.2f}, angular={self.angular_speed:.2f})"
        )

    def read_key(self):
        tty.setraw(sys.stdin.fileno())
        try:
            ready, _, _ = select.select([sys.stdin], [], [], 0.1)
            if ready:
                return sys.stdin.read(1)
            return ""
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

    def publish_command(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher.publish(msg)
        self.get_logger().info(
            f"cmd -> linear.x={msg.linear.x:.2f}, angular.z={msg.angular.z:.2f}"
        )

    def run(self):
        try:
            while rclpy.ok():
                key = self.read_key()
                if not key:
                    continue
                if key == "\x03":
                    break
                if key in SPEED_BINDINGS:
                    linear_scale, angular_scale = SPEED_BINDINGS[key]
                    self.linear_speed *= linear_scale
                    self.angular_speed *= angular_scale
                    self.get_logger().info(
                        f"speed updated: linear={self.linear_speed:.2f}, "
                        f"angular={self.angular_speed:.2f}"
                    )
                    continue
                if key == "k":
                    self.publish_command(0.0, 0.0)
                    continue
                if key in MOVE_BINDINGS:
                    linear_sign, angular_sign = MOVE_BINDINGS[key]
                    self.publish_command(
                        self.linear_speed * linear_sign,
                        self.angular_speed * angular_sign,
                    )
        finally:
            self.publish_command(0.0, 0.0)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)


def main(args=None):
    rclpy.init(args=args)
    node = TeleopKeyboard()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
