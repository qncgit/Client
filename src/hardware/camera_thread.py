import cv2
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from pyzbar.pyzbar import decode
import time

class CameraThread(QThread):
    """
    Luồng riêng để xử lý video từ camera, tránh làm treo giao diện chính.
    """
    frame_update = pyqtSignal(QImage)
    qr_decoded = pyqtSignal(str)

    def __init__(self, config_manager):
        super().__init__()
        self._config = config_manager
        self._is_running = False
        self.cap = None
        self._last_qr_data = None
        self._last_qr_time = 0
        self._qr_cooldown = 3

    def _initialize_camera(self):
        """Khởi tạo camera dựa trên cấu hình."""
        cam_type = self._config.get('camera.qr.type', 'webcam')
        if cam_type == 'webcam':
            cam_index = self._config.get('camera.qr.webcam.index', 0)
            self.cap = cv2.VideoCapture(cam_index)
        else:
            rtsp_url = self._config.get('camera.qr.rtsp.url', '')
            self.cap = cv2.VideoCapture(rtsp_url)
        
        if not self.cap or not self.cap.isOpened():
            print("Lỗi: Không thể mở camera.")
            self.cap = None

    def run(self):
        self._is_running = True
        if not self._config.get('camera.qr.enabled', False):
            print("Camera QR bị tắt trong config.")
            self._is_running = False
            return

        self._initialize_camera()

        if not self.cap:
            self._is_running = False

        while self._is_running:
            if not self.cap.isOpened():
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            try:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_update.emit(qt_image)
            except cv2.error:
                continue

            try:
                decoded_objects = decode(frame)
                if decoded_objects:
                    qr_data = decoded_objects[0].data.decode('utf-8')
                    current_time = time.time()
                    if qr_data != self._last_qr_data or (current_time - self._last_qr_time) > self._qr_cooldown:
                        self._last_qr_data = qr_data
                        self._last_qr_time = current_time
                        self.qr_decoded.emit(qr_data)
            except Exception as e:
                print(f"Lỗi khi giải mã QR: {e}")

            time.sleep(0.05)

        if self.cap:
            self.cap.release()
        print("Luồng camera đã dừng.")

    def stop(self):
        self._is_running = False
        self.wait(2000)
