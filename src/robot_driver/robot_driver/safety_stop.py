import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class SafetyStop(Node):
    def __init__(self):
        super().__init__("safety_stop")
        self.input_topic = str(self.declare_parameter("input_topic", "/cmd_vel_raw").value)
        self.output_topic = str(self.declare_parameter("output_topic", "/cmd_vel").value)
        self.scan_topic = str(self.declare_parameter("scan_topic", "/scan").value)
        self.safety_distance = float(self.declare_parameter("safety_distance", 0.5).value)
        self.angle_range_deg = float(self.declare_parameter("angle_range_deg", 60.0).value)

        self.create_subscription(Twist, self.input_topic, self.cmd_callback, 10)
        self.create_subscription(LaserScan, self.scan_topic, self.scan_callback, 10)
        self.publisher = self.create_publisher(Twist, self.output_topic, 10)

        self.obstacle_detected = False
        self.last_min_distance = math.inf
        self.get_logger().info(
            f"Safety stop active on {self.scan_topic}: threshold={self.safety_distance}m"
        )

    def scan_callback(self, msg):
        half_angle = math.radians(self.angle_range_deg) / 2.0
        min_distance = math.inf
        for index, distance in enumerate(msg.ranges):
            if math.isinf(distance) or math.isnan(distance) or distance <= 0.0:
                continue
            angle = msg.angle_min + index * msg.angle_increment
            if -half_angle <= angle <= half_angle:
                min_distance = min(min_distance, distance)
        self.last_min_distance = min_distance
        self.obstacle_detected = min_distance < self.safety_distance

    def cmd_callback(self, msg):
        if self.obstacle_detected and msg.linear.x > 0.0:
            blocked = Twist()
            self.publisher.publish(blocked)
            self.get_logger().warn(
                f"Obstacle ahead at {self.last_min_distance:.2f}m, blocking forward command"
            )
            return
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyStop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
