import re
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import Image


class RoiFollower(Node):
    def __init__(self):
        super().__init__("roi_follower")
        self.image_topic = str(self.declare_parameter("image_topic", "/image_raw").value)
        self.video_device = str(self.declare_parameter("video_device", "").value)
        self.frame_width = int(self.declare_parameter("frame_width", 640).value)
        self.frame_height = int(self.declare_parameter("frame_height", 480).value)
        self.fps = float(self.declare_parameter("fps", 30.0).value)
        self.output_topic = str(self.declare_parameter("output_topic", "/cmd_vel").value)
        self.window_name = str(self.declare_parameter("window_name", "ROI Follower").value)
        self.max_linear = float(self.declare_parameter("max_linear", 7.0).value)
        self.max_angular = float(self.declare_parameter("max_angular", 24.0).value)
        self.linear_gain = float(self.declare_parameter("linear_gain", 24.0).value)
        self.angular_gain = float(self.declare_parameter("angular_gain", 32.0).value)
        self.target_area_ratio = float(self.declare_parameter("target_area_ratio", 0.16).value)
        self.center_deadband = float(self.declare_parameter("center_deadband", 0.08).value)
        self.min_box_area = int(self.declare_parameter("min_box_area", 900).value)
        self.motion_enabled = bool(self.declare_parameter("motion_enabled", True).value)

        self.publisher = self.create_publisher(Twist, self.output_topic, 10)
        self.subscription = None
        self.capture = None
        self.capture_timer = None
        self.capture_thread = None
        self.capture_stop = threading.Event()
        self.frame_lock = threading.Lock()
        self.pending_frame: Optional[np.ndarray] = None
        self.last_capture_warning = 0.0

        self.latest_frame: Optional[np.ndarray] = None
        self.track_window: Optional[Tuple[int, int, int, int]] = None
        self.roi_hist: Optional[np.ndarray] = None
        self.last_cmd = (None, None)
        self.term_crit = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            10,
            1,
        )

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self.get_logger().info(
            "ROI follower ready. Press 's' to select a target, 'c' to clear it, "
            "'m' to toggle motion, 'x' to stop, 'q' to quit the window."
        )
        if self.video_device:
            self.open_capture()
        else:
            self.subscription = self.create_subscription(Image, self.image_topic, self.on_image, 10)
            self.get_logger().info(
                f"Tracking {self.image_topic} and publishing follow commands to {self.output_topic}"
            )

    def on_image(self, msg: Image):
        frame = self.image_to_mat(msg)
        self.process_frame(frame)

    def open_capture(self):
        source = self.normalize_capture_source(self.video_device)
        self.capture = cv2.VideoCapture(source, cv2.CAP_V4L2)
        if not self.capture.isOpened():
            self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            self.get_logger().error(f"Failed to open video_device={self.video_device}")
            return
        if hasattr(cv2, "CAP_PROP_BUFFERSIZE"):
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        self.capture_timer = self.create_timer(1.0 / max(self.fps, 1.0), self.poll_capture)
        self.get_logger().info(
            f"Tracking video_device={self.video_device} and publishing follow commands to "
            f"{self.output_topic}"
        )

    @staticmethod
    def normalize_capture_source(video_device: str):
        match = re.fullmatch(r"/dev/video(\d+)", video_device)
        if match:
            return int(match.group(1))
        return video_device

    def capture_loop(self):
        while not self.capture_stop.is_set() and self.capture is not None:
            ok, frame = self.capture.read()
            if not ok or frame is None:
                now = time.time()
                if now - self.last_capture_warning > 1.0:
                    self.last_capture_warning = now
                    self.get_logger().warn("Failed to read frame from video device.")
                time.sleep(0.02)
                continue
            with self.frame_lock:
                self.pending_frame = frame

    def poll_capture(self):
        if self.capture is None:
            return
        with self.frame_lock:
            frame = None if self.pending_frame is None else self.pending_frame.copy()
        if frame is None:
            return
        self.process_frame(frame)

    def process_frame(self, frame: np.ndarray):
        self.latest_frame = frame.copy()
        display = frame.copy()
        status = "idle"

        if self.track_window is not None and self.roi_hist is not None:
            updated = self.update_tracking(frame)
            if updated is None:
                self.clear_tracking(stop_robot=True)
                status = "lost"
            else:
                center_x, center_y, width, height = updated
                status = "tracking"
                self.draw_tracking(display, center_x, center_y, width, height)
                if self.motion_enabled:
                    self.publish_follow_command(frame.shape[1], frame.shape[0], center_x, width, height)
                else:
                    self.publish_stop_if_needed()
        else:
            self.publish_stop_if_needed()

        self.draw_overlay(display, status)
        cv2.imshow(self.window_name, display)
        self.handle_keyboard()

    def handle_keyboard(self):
        key = cv2.waitKey(1) & 0xFF
        if key == ord("s") and self.latest_frame is not None:
            self.select_roi()
        elif key == ord("c"):
            self.clear_tracking(stop_robot=True)
        elif key == ord("m"):
            self.motion_enabled = not self.motion_enabled
            self.get_logger().info(f"motion_enabled={self.motion_enabled}")
            if not self.motion_enabled:
                self.publish_stop_if_needed()
        elif key == ord("x"):
            self.publish_stop(force=True)
        elif key == ord("q"):
            self.clear_tracking(stop_robot=True)
            rclpy.shutdown()

    def select_roi(self):
        selection = cv2.selectROI(
            self.window_name,
            self.latest_frame,
            showCrosshair=False,
            fromCenter=False,
        )
        x, y, w, h = [int(v) for v in selection]
        if w * h < self.min_box_area:
            self.get_logger().warn("ROI too small, selection ignored.")
            return

        roi = self.latest_frame[y : y + h, x : x + w]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_roi, np.array((0.0, 30.0, 20.0)), np.array((180.0, 255.0, 255.0)))
        roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
        cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

        self.track_window = (x, y, w, h)
        self.roi_hist = roi_hist
        self.get_logger().info(f"ROI selected: x={x}, y={y}, w={w}, h={h}")

    def update_tracking(self, frame: np.ndarray):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        back_proj = cv2.calcBackProject([hsv], [0], self.roi_hist, [0, 180], 1)
        _, track_window = cv2.CamShift(back_proj, self.track_window, self.term_crit)
        x, y, w, h = [int(v) for v in track_window]
        frame_h, frame_w = frame.shape[:2]
        x = max(0, min(x, frame_w - 1))
        y = max(0, min(y, frame_h - 1))
        w = max(0, min(w, frame_w - x))
        h = max(0, min(h, frame_h - y))
        if w * h < self.min_box_area:
            return None

        self.track_window = (x, y, w, h)
        center_x = x + (w / 2.0)
        center_y = y + (h / 2.0)
        return center_x, center_y, w, h

    def draw_tracking(self, frame: np.ndarray, center_x: float, center_y: float, width: int, height: int):
        x = int(center_x - (width / 2.0))
        y = int(center_y - (height / 2.0))
        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
        cv2.circle(frame, (int(center_x), int(center_y)), 4, (0, 255, 255), -1)
        cv2.line(
            frame,
            (frame.shape[1] // 2, 0),
            (frame.shape[1] // 2, frame.shape[0]),
            (255, 0, 0),
            1,
        )

    def publish_follow_command(
        self,
        frame_width: int,
        frame_height: int,
        center_x: float,
        box_width: int,
        box_height: int,
    ):
        center_error = (center_x - (frame_width / 2.0)) / (frame_width / 2.0)
        if abs(center_error) < self.center_deadband:
            center_error = 0.0

        box_ratio = float(box_width * box_height) / float(frame_width * frame_height)
        distance_error = self.target_area_ratio - box_ratio

        linear = self.clamp(distance_error * self.linear_gain, self.max_linear)
        angular = self.clamp(-center_error * self.angular_gain, self.max_angular)
        self.publish_cmd(linear, angular)

    def draw_overlay(self, frame: np.ndarray, status: str):
        lines = [
            f"status: {status}",
            f"motion: {'on' if self.motion_enabled else 'off'}",
            "s select  c clear  m motion  x stop  q close",
        ]
        for index, text in enumerate(lines):
            cv2.putText(
                frame,
                text,
                (10, 25 + index * 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

    def clear_tracking(self, stop_robot: bool):
        self.track_window = None
        self.roi_hist = None
        if stop_robot:
            self.publish_stop(force=True)

    def publish_stop_if_needed(self):
        self.publish_stop(force=False)

    def publish_stop(self, force: bool):
        if force or self.last_cmd != (0.0, 0.0):
            self.publish_cmd(0.0, 0.0)

    def publish_cmd(self, linear: float, angular: float):
        linear = self.clamp(linear, self.max_linear)
        angular = self.clamp(angular, self.max_angular)
        rounded = (round(linear, 3), round(angular, 3))
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.publisher.publish(msg)
        if rounded != self.last_cmd:
            self.last_cmd = rounded
            self.get_logger().info(
                f"cmd_vel -> linear.x={msg.linear.x:.2f}, angular.z={msg.angular.z:.2f}"
            )

    @staticmethod
    def clamp(value: float, limit: float) -> float:
        return max(min(value, limit), -limit)

    @staticmethod
    def image_to_mat(msg: Image) -> np.ndarray:
        if msg.encoding == "bgr8":
            frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step // 3, 3))
            return frame[:, : msg.width, :].copy()
        if msg.encoding == "rgb8":
            frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step // 3, 3))
            frame = frame[:, : msg.width, :]
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if msg.encoding == "mono8":
            frame = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.step))
            gray = frame[:, : msg.width]
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        raise ValueError(f"Unsupported encoding: {msg.encoding}")

    def destroy_node(self):
        self.publish_stop(force=True)
        try:
            self.capture_stop.set()
            if self.capture_thread is not None:
                self.capture_thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self.capture is not None:
                self.capture.release()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RoiFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
