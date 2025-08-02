# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/widgets/bottom_widget.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout
# ✨ SỬA ĐỔI: Import thêm pyqtSignal
from PyQt5.QtCore import Qt, pyqtSignal
# ✨ SỬA ĐỔI: Import thêm TransparentToolButton và sử dụng alias FIF
from qfluentwidgets import (ProgressBar, IconWidget, CaptionLabel, BodyLabel, 
                          FluentIcon as FIF, TransparentToolButton, InfoBar)

class BottomWidget(QWidget):
    # ✨ SỬA ĐỔI: Thêm tín hiệu để báo cho cửa sổ chính khi nút được nhấn
    settings_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)

        # ✨ SỬA ĐỔI: Tạo nút cài đặt
        self.settings_button = TransparentToolButton(FIF.SETTING, self)
        self.settings_button.setToolTip("Mở cài đặt hệ thống")
        # Kết nối sự kiện click của nút với tín hiệu của widget
        self.settings_button.clicked.connect(self.settings_button_clicked.emit)

        # Trạng thái máy chủ và cân
        self.server_status_icon = IconWidget(FIF.CONNECT)
        self.server_status_label = BodyLabel("Máy chủ: OK")
        
        self.weight_status_icon = IconWidget(FIF.CONNECT)
        self.weight_status_label = BodyLabel("Đầu cân: OK")

        self.set_server_status(True, "Khởi tạo...")
        self.set_weight_status(True, "Khởi tạo...")

        self.status_label = BodyLabel("Trạng thái: Sẵn sàng quét mã lệnh.")
        reset_label = BodyLabel("⏱")
        self.reset_progress = ProgressBar(self)
        self.reset_progress.setFixedWidth(150)
        self.reset_progress.setFixedHeight(4)
        self.reset_progress.setRange(0, 100)
        self.reset_progress.setValue(0)
        self.reset_progress.setTextVisible(False)
        self.reset_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background: #f0f0f0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
        
        self.countdown_label = CaptionLabel("")
        self.countdown_label.setFixedWidth(50)

        # ✨ SỬA ĐỔI: Thêm nút cài đặt vào layout ở vị trí đầu tiên bên trái
        layout.addWidget(self.settings_button)
        layout.addSpacing(15)

        layout.addWidget(self.server_status_icon)
        layout.addWidget(self.server_status_label)
        layout.addSpacing(15)
        layout.addWidget(self.weight_status_icon)
        layout.addWidget(self.weight_status_label)
        layout.addSpacing(15)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(reset_label)
        layout.addWidget(self.reset_progress)
        layout.addWidget(self.countdown_label)

    # ... các hàm còn lại giữ nguyên ...
    def set_status(self, text, color="black"):
        self.status_label.setText(f"Trạng thái: {text}")
        self.status_label.setStyleSheet(f"color: {color};")

    def set_server_status(self, is_connected, message=""):
        icon = FIF.CONNECT if is_connected else FIF.ERROR
        self.server_status_icon.setIcon(icon)
        self.server_status_label.setText("Máy chủ: OK" if is_connected else "Máy chủ: Lỗi")
        self.server_status_label.setStyleSheet("color: #008000;" if is_connected else "color: #d32f2f;")

    def set_weight_status(self, is_connected, message=""):
        icon = FIF.CONNECT if is_connected else FIF.ERROR
        self.weight_status_icon.setIcon(icon)
        self.weight_status_label.setText("Đầu cân: OK" if is_connected else "Đầu cân: Lỗi")
        self.weight_status_label.setStyleSheet("color: #008000;" if is_connected else "color: #d32f2f;")

    def update_progress(self, value, remaining_seconds):
        """Cập nhật giá trị progress bar và label đếm ngược"""
        if remaining_seconds > 0:
            progress_value = max(0, min(100, value))
            self.reset_progress.setValue(progress_value)
            self.countdown_label.setText(f"{int(remaining_seconds)}s")
            
            # Đổi màu dựa theo tiến trình (ngược lại so với trước)
            if progress_value > 70:
                chunk_color = "#2ecc71"  # Xanh lá khi còn nhiều thời gian
            elif progress_value > 30:
                chunk_color = "#f1c40f"  # Vàng khi còn một nửa
            else:
                chunk_color = "#e74c3c"  # Đỏ khi sắp hết thời gian
        else:
            # Hiển thị mặc định khi không có đếm ngược: sẵn sàng với 15s
            progress_value = 100
            self.reset_progress.setValue(progress_value)
            self.countdown_label.setText("15s")
            chunk_color = "#cccccc"  # Màu xám cho trạng thái chờ
        
        self.reset_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background: #f0f0f0;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 2px;
            }}
        """)
        
        # Luôn hiển thị progress bar và label
        self.reset_progress.setVisible(True)
        self.countdown_label.setVisible(True)