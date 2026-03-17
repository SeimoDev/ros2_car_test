import threading
import time
from pathlib import Path

import rclpy
import serial
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import String


FIELD_INDEX = {
    "vx": 0,
    "vy": 1,
    "aux": 2,
    "wz": 3,
}


class TestMotor(Node):
    def __init__(self):
        super().__init__("test_motor")
        self.serial_port = str(self.declare_parameter("serial_port", "/dev/ttyUSB0").value)
        self.baudrate = int(self.declare_parameter("baudrate", 115200).value)
        self.linear_scale = int(self.declare_parameter("linear_scale", 100).value)
        self.angular_scale = int(self.declare_parameter("angular_scale", 100).value)
        self.max_linear = float(self.declare_parameter("max_linear", 0.6).value)
        self.max_angular = float(self.declare_parameter("max_angular", 1.5).value)
        self.send_rate = float(self.declare_parameter("send_rate", 20.0).value)
        self.timeout = float(self.declare_parameter("serial_timeout", 0.05).value)
        self.linear_field = str(self.declare_parameter("linear_field", "vy").value)
        self.angular_field = str(self.declare_parameter("angular_field", "vx").value)
        self.reverse_angular = bool(self.declare_parameter("reverse_angular", False).value)
        self.serial_handle = None
        self.latest_cmd = Twist()
        self.latest_cmd_time = time.time()
        self.raw_pub = self.create_publisher(String, "/robot_driver/raw_status", 10)
        self.create_subscription(Twist, "/cmd_vel", self.cmd_callback, 10)
        self.timer = self.create_timer(1.0 / self.send_rate, self.send_latest_command)
        self._stop_event = threading.Event()
        self._reader = None
        self._last_logged_cmd = None

        self.get_logger().warn(
            "Using inferred 0x7b ... 0x7d STM32 chassis protocol. "
            "Keep the car lifted while calibrating field mappings."
        )
        self.get_logger().info(
            f"motor serial_port={self.serial_port}, baudrate={self.baudrate}, "
            f"linear_field={self.linear_field}, angular_field={self.angular_field}, "
            f"exists={Path(self.serial_port).exists()}"
        )

        self.open_serial()

    def open_serial(self):
        try:
            self.serial_handle = serial.Serial(
                self.serial_port,
                self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            self.get_logger().info(f"Opened motor serial: {self.serial_port}@{self.baudrate}")
            self._reader = threading.Thread(target=self.read_loop, daemon=True)
            self._reader.start()
        except Exception as exc:
            self.get_logger().error(f"Failed to open motor serial {self.serial_port}: {exc}")
            self.serial_handle = None

    def cmd_callback(self, msg):
        self.latest_cmd = msg
        self.latest_cmd_time = time.time()
        key = (round(msg.linear.x, 3), round(msg.angular.z, 3))
        if key != self._last_logged_cmd:
            self._last_logged_cmd = key
            self.get_logger().info(
                f"cmd_vel -> linear.x={msg.linear.x:.2f}, angular.z={msg.angular.z:.2f}"
            )

    @staticmethod
    def clamp(value, limit):
        return max(min(value, limit), -limit)

    @staticmethod
    def int16_to_bytes(value):
        value &= 0xFFFF
        return [(value >> 8) & 0xFF, value & 0xFF]

    def build_frame(self, linear_x, angular_z):
        fields = [0, 0, 0, 0]
        linear_value = int(self.clamp(linear_x, self.max_linear) * self.linear_scale)
        angular_value = int(self.clamp(angular_z, self.max_angular) * self.angular_scale)
        if self.reverse_angular:
            angular_value = -angular_value

        if self.linear_field not in FIELD_INDEX or self.angular_field not in FIELD_INDEX:
            raise ValueError("linear_field/angular_field must be one of vx, vy, aux, wz")

        fields[FIELD_INDEX[self.linear_field]] = linear_value
        fields[FIELD_INDEX[self.angular_field]] = angular_value

        payload = []
        for field in fields:
            payload.extend(self.int16_to_bytes(field))

        checksum = 0x7B
        for byte in payload:
            checksum ^= byte
        return bytes([0x7B, *payload, checksum, 0x7D])

    def send_latest_command(self):
        if self.serial_handle is None:
            return

        cmd = self.latest_cmd
        if time.time() - self.latest_cmd_time > 1.0:
            cmd = Twist()

        try:
            frame = self.build_frame(cmd.linear.x, cmd.angular.z)
            self.serial_handle.write(frame)
        except Exception as exc:
            self.get_logger().error(f"Failed to write motor frame: {exc}")

    def read_loop(self):
        buffer = bytearray()
        while not self._stop_event.is_set() and self.serial_handle is not None:
            try:
                chunk = self.serial_handle.read(64)
            except Exception as exc:
                self.get_logger().error(f"Serial read failed: {exc}")
                return
            if not chunk:
                continue
            buffer.extend(chunk)
            while True:
                start = buffer.find(b"\x7b")
                if start < 0:
                    buffer.clear()
                    break
                end = buffer.find(b"\x7d", start + 1)
                if end < 0:
                    if start > 0:
                        del buffer[:start]
                    break
                frame = bytes(buffer[start:end + 1])
                del buffer[: end + 1]
                hex_frame = " ".join(f"{byte:02x}" for byte in frame)
                self.raw_pub.publish(String(data=hex_frame))

    def destroy_node(self):
        self._stop_event.set()
        try:
            if self.serial_handle is not None:
                stop_frame = self.build_frame(0.0, 0.0)
                self.serial_handle.write(stop_frame)
                self.serial_handle.close()
        except Exception:
            pass
        super().destroy_node()


def main():
    rclpy.init()
    node = TestMotor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
