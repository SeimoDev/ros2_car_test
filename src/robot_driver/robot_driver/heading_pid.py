import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node


class HeadingPid(Node):
    def __init__(self):
        super().__init__("heading_pid")
        self.input_topic = str(self.declare_parameter("input_topic", "/cmd_vel_raw").value)
        self.output_topic = str(self.declare_parameter("output_topic", "/cmd_vel").value)
        self.odom_topic = str(self.declare_parameter("odom_topic", "/odom").value)
        self.p = float(self.declare_parameter("p", 1.5).value)
        self.i = float(self.declare_parameter("i", 0.0).value)
        self.d = float(self.declare_parameter("d", 0.1).value)
        self.max_correction = float(self.declare_parameter("max_correction", 1.5).value)
        self.min_linear_speed = float(self.declare_parameter("min_linear_speed", 0.05).value)
        self.straight_angular_threshold = float(
            self.declare_parameter("straight_angular_threshold", 0.05).value
        )
        self.heading_deadband = float(self.declare_parameter("heading_deadband", 0.01).value)
        self.command_timeout = float(self.declare_parameter("command_timeout", 1.0).value)
        self.update_rate = float(self.declare_parameter("update_rate", 20.0).value)

        self.create_subscription(Twist, self.input_topic, self.cmd_callback, 10)
        self.create_subscription(Odometry, self.odom_topic, self.odom_callback, 10)
        self.publisher = self.create_publisher(Twist, self.output_topic, 10)
        self.add_on_set_parameters_callback(self.on_parameters_changed)

        self.latest_cmd = Twist()
        self.latest_cmd_time = self.get_clock().now()
        self.current_yaw = None
        self.target_heading = None
        self.integral = 0.0
        self.last_error = 0.0
        self.last_control_time = self.get_clock().now()

        self.create_timer(1.0 / self.update_rate, self.control_loop)
        self.get_logger().info(
            f"Heading PID enabled on {self.input_topic} -> {self.output_topic} "
            f"(p={self.p}, i={self.i}, d={self.d})"
        )

    def cmd_callback(self, msg):
        self.latest_cmd = msg
        self.latest_cmd_time = self.get_clock().now()

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def on_parameters_changed(self, params):
        for param in params:
            if param.name in {"p", "i", "d", "max_correction"}:
                setattr(self, param.name, float(param.value))
        return SetParametersResult(successful=True)

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def reset_controller(self):
        self.target_heading = None
        self.integral = 0.0
        self.last_error = 0.0

    def get_effective_cmd(self, now):
        age = (now - self.latest_cmd_time).nanoseconds / 1e9
        return self.latest_cmd if age <= self.command_timeout else Twist()

    def control_loop(self):
        now = self.get_clock().now()
        dt = (now - self.last_control_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        cmd = self.get_effective_cmd(now)
        output = Twist()
        output.linear.x = cmd.linear.x
        output.linear.y = cmd.linear.y
        output.angular.z = cmd.angular.z

        straight_drive = (
            self.current_yaw is not None
            and abs(cmd.linear.x) >= self.min_linear_speed
            and abs(cmd.angular.z) <= self.straight_angular_threshold
        )

        if straight_drive:
            if self.target_heading is None:
                self.target_heading = self.current_yaw
                self.integral = 0.0
                self.last_error = 0.0

            error = self.normalize_angle(self.target_heading - self.current_yaw)
            if abs(error) < self.heading_deadband:
                error = 0.0
            self.integral += error * dt
            derivative = (error - self.last_error) / dt
            correction = self.p * error + self.i * self.integral + self.d * derivative
            correction = max(min(correction, self.max_correction), -self.max_correction)
            output.angular.z += correction
            self.last_error = error
        else:
            self.reset_controller()

        self.publisher.publish(output)
        self.last_control_time = now


def main(args=None):
    rclpy.init(args=args)
    node = HeadingPid()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
