import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraViewer(Node):
    def __init__(self):
        super().__init__("camera_viewer")
        self.topic = self.declare_parameter("image_topic", "/image_raw").value
        self.window_name = self.declare_parameter("window_name", "Jetson Camera").value
        self.subscription = self.create_subscription(Image, self.topic, self.handle_image, 10)
        self.get_logger().info(f"Subscribed to image topic: {self.topic}")

    def handle_image(self, msg):
        try:
            frame = self.image_to_mat(msg)
            cv2.imshow(self.window_name, frame)
            cv2.waitKey(1)
        except Exception as exc:
            self.get_logger().error(f"Failed to display image: {exc}")

    @staticmethod
    def image_to_mat(msg):
        if msg.encoding not in ("bgr8", "rgb8", "mono8"):
            raise ValueError(f"Unsupported encoding: {msg.encoding}")

        if msg.encoding == "mono8":
            frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step))
            return frame[:, :msg.width]

        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step // 3, 3))
        frame = frame[:, :msg.width, :]
        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame


def main():
    rclpy.init()
    node = CameraViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
