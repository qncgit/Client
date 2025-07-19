from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QToolButton, QStyle
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

class BottomWidget(QWidget):
    """
    Widget phần Footer, được viết lại để khớp với thiết kế gốc.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        # Sử dụng icon chuẩn của Qt
        server_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        weight_icon = self.style().standardIcon(QStyle.SP_DriveHDIcon) # Icon tạm thời

        self.server_status_label = self._create_status_indicator(server_icon, "Máy chủ: OK")
        self.weight_status_label = self._create_status_indicator(weight_icon, "Đầu cân: OK")

        self.status_label = QLabel("Trạng thái: Sẵn sàng quét mã lệnh.")
        self.status_label.setStyleSheet("font-size: 10pt; font-weight: bold;")

        reset_label = QLabel("Reset:")
        reset_label.setStyleSheet("font-size: 10pt;")

        self.reset_progress_bar = QProgressBar()
        self.reset_progress_bar.setTextVisible(False)
        self.reset_progress_bar.setRange(0, 100)
        self.reset_progress_bar.setValue(0)
        self.reset_progress_bar.setFixedSize(150, 18)
        self.reset_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3add36;
                width: 1px;
            }
        """)

        self.countdown_label = QLabel("")
        self.countdown_label.setFixedWidth(50)
        self.countdown_label.setStyleSheet("font-size: 10pt; font-weight: bold;")

        layout.addWidget(self.server_status_label)
        layout.addSpacing(15)
        layout.addWidget(self.weight_status_label)
        layout.addSpacing(15)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(reset_label)
        layout.addWidget(self.reset_progress_bar)
        layout.addWidget(self.countdown_label)

    def _create_status_indicator(self, icon, text):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(QSize(16,16)))

        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #008000;")
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        
        container.text_label = text_label # Lưu lại để cập nhật text
        return container

    # SỬA LỖI: Thêm lại hàm set_status còn thiếu
    def set_status(self, text, color="black"):
        self.status_label.setText(f"Trạng thái: {text}")
        self.status_label.setStyleSheet(f"font-size: 10pt; font-weight: bold; color: {color};")

    def set_server_status(self, is_connected):
        if is_connected:
            self.server_status_label.text_label.setText("Máy chủ: OK")
            self.server_status_label.text_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #008000;")
        else:
            self.server_status_label.text_label.setText("Máy chủ: Lỗi")
            self.server_status_label.text_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #d32f2f;")

    def set_weight_status(self, is_connected):
        if is_connected:
            self.weight_status_label.text_label.setText("Đầu cân: OK")
            self.weight_status_label.text_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #008000;")
        else:
            self.weight_status_label.text_label.setText("Đầu cân: Lỗi")
            self.weight_status_label.text_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #d32f2f;")

    def update_progress(self, value, remaining_seconds):
        self.reset_progress_bar.setValue(value)
        if value > 0:
            self.countdown_label.setText(f"{int(remaining_seconds)} giây")
        else:
            self.countdown_label.setText("")
