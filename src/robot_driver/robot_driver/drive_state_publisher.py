import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
from tf2_ros import TransformBroadcaster


class DriveStatePublisher(Node):
    def __init__(self):
        super().__init__("drive_state_publisher")
        self.command_topic = str(self.declare_parameter("command_topic", "/cmd_vel").value)
        self.odom_topic = str(self.declare_parameter("odom_topic", "/odom").value)
        self.imu_topic = str(self.declare_parameter("imu_topic", "/imu/data_raw").value)
        self.battery_topic = str(
            self.declare_parameter("battery_topic", "/battery_voltage").value
        )
        self.raw_speed_topic = str(
            self.declare_parameter("raw_speed_topic", "/robot_driver/raw_speed").value
        )
        self.odom_frame = str(self.declare_parameter("odom_frame", "odom").value)
        self.base_frame = str(self.declare_parameter("base_frame", "base_link").value)
        self.imu_frame = str(self.declare_parameter("imu_frame", "imu_link").value)
        self.update_rate = float(self.declare_parameter("update_rate", 20.0).value)
        self.publish_tf = bool(self.declare_parameter("publish_tf", True).value)
        self.command_timeout = float(self.declare_parameter("command_timeout", 1.0).value)
        self.initial_battery_voltage = float(
            self.declare_parameter("initial_battery_voltage", 12.3).value
        )
        self.minimum_battery_voltage = float(
            self.declare_parameter("minimum_battery_voltage", 11.0).value
        )
        self.battery_drain_rate = float(
            self.declare_parameter("battery_drain_rate", 0.002).value
        )

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.imu_pub = self.create_publisher(Imu, self.imu_topic, 10)
        self.battery_pub = self.create_publisher(Float32, self.battery_topic, 10)
        self.raw_speed_pub = self.create_publisher(TwistStamped, self.raw_speed_topic, 10)
        self.create_subscription(Twist, self.command_topic, self.cmd_callback, 10)
        self.tf_broadcaster = TransformBroadcaster(self) if self.publish_tf else None

        self.current_cmd = Twist()
        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.last_update = self.get_clock().now()
        self.battery_voltage = self.initial_battery_voltage
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.create_timer(1.0 / self.update_rate, self.update)
        self.get_logger().info(
            f"Publishing {self.odom_topic}, {self.imu_topic}, {self.battery_topic} "
            f"from open-loop integration of {self.command_topic}"
        )

    def cmd_callback(self, msg):
        self.current_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def yaw_to_quaternion(yaw):
        z = math.sin(yaw / 2.0)
        w = math.cos(yaw / 2.0)
        return z, w

    def get_effective_cmd(self, now):
        age = (now - self.last_cmd_time).nanoseconds / 1e9
        return self.current_cmd if age <= self.command_timeout else Twist()

    def update(self):
        now = self.get_clock().now()
        dt = (now - self.last_update).nanoseconds / 1e9
        if dt <= 0.0:
            return

        cmd = self.get_effective_cmd(now)

        vx_body = cmd.linear.x
        vy_body = cmd.linear.y
        wz = cmd.angular.z

        self.x += (vx_body * math.cos(self.yaw) - vy_body * math.sin(self.yaw)) * dt
        self.y += (vx_body * math.sin(self.yaw) + vy_body * math.cos(self.yaw)) * dt
        self.yaw = self.normalize_angle(self.yaw + wz * dt)

        accel_x = (vx_body - self.last_cmd.linear.x) / dt
        accel_y = (vy_body - self.last_cmd.linear.y) / dt
        z, w = self.yaw_to_quaternion(self.yaw)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = z
        odom.pose.pose.orientation.w = w
        odom.twist.twist.linear.x = vx_body
        odom.twist.twist.linear.y = vy_body
        odom.twist.twist.angular.z = wz
        self.odom_pub.publish(odom)

        imu = Imu()
        imu.header.stamp = now.to_msg()
        imu.header.frame_id = self.imu_frame
        imu.orientation.z = z
        imu.orientation.w = w
        imu.angular_velocity.z = wz
        imu.linear_acceleration.x = accel_x
        imu.linear_acceleration.y = accel_y
        imu.linear_acceleration.z = 9.81
        self.imu_pub.publish(imu)

        raw_speed = TwistStamped()
        raw_speed.header.stamp = now.to_msg()
        raw_speed.header.frame_id = self.base_frame
        raw_speed.twist.linear.x = vx_body
        raw_speed.twist.linear.y = vy_body
        raw_speed.twist.angular.z = wz
        self.raw_speed_pub.publish(raw_speed)

        load = abs(vx_body) + abs(vy_body) + 0.2 * abs(wz)
        self.battery_voltage = max(
            self.minimum_battery_voltage,
            self.battery_voltage - self.battery_drain_rate * load * dt,
        )
        battery = Float32()
        battery.data = self.battery_voltage
        self.battery_pub.publish(battery)

        if self.tf_broadcaster is not None:
            transform = TransformStamped()
            transform.header.stamp = now.to_msg()
            transform.header.frame_id = self.odom_frame
            transform.child_frame_id = self.base_frame
            transform.transform.translation.x = self.x
            transform.transform.translation.y = self.y
            transform.transform.rotation.z = z
            transform.transform.rotation.w = w
            self.tf_broadcaster.sendTransform(transform)

        self.last_cmd = cmd
        self.last_update = now


def main(args=None):
    rclpy.init(args=args)
    node = DriveStatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
