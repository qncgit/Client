from PyQt5.QtWidgets import QLabel, QVBoxLayout, QGridLayout, QFrame, QLineEdit, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class BaseStepWidget(QFrame):
    """
    Lớp cơ sở cho các widget hiển thị thông tin, được viết lại để khớp thiết kế.
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: white; background-color: #00557f; padding: 8px; border-top-left-radius: 8px; border-top-right-radius: 8px;")

        self.content_widget = QFrame()
        self.content_widget.setFrameShape(QFrame.StyledPanel)
        self.content_widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #00557f;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.content_widget)

        self.info_fields = {}

    def _add_info_row(self, layout, key, label_text, row, col):
        """Thêm một hàng thông tin vào layout dạng lưới, giống thiết kế gốc."""
        label = QLabel(f"{label_text}:")
        label.setStyleSheet("font-weight: bold; color: #333; font-size: 9pt;")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        value_field = QLabel("-")
        value_field.setStyleSheet("font-size: 9pt; color: #000; border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f0f0f0;")
        value_field.setMinimumHeight(28)

        layout.addWidget(label, row, col * 2)
        layout.addWidget(value_field, row, col * 2 + 1)
        self.info_fields[key] = value_field

    def update_info(self, data_dict):
        if not data_dict:
            self.reset()
            return
        for key, field in self.info_fields.items():
            value = data_dict.get(key, '-')
            field.setText(str(value) if value is not None else '-')

    def reset(self):
        for field in self.info_fields.values():
            field.setText("-")


class Step1_QRScanWidget(BaseStepWidget):
    """Bước 1: Hiển thị camera và thông tin lệnh cân."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 1: THÔNG TIN LỆNH VẬN CHUYỂN (QUÉT QR)", parent)

        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)

        self.camera_view = QLabel("ĐANG KẾT NỐI CAMERA...")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setMinimumSize(320, 240)
        self.camera_view.setStyleSheet("color: white; font-weight: bold; font-size: 14pt; background-color: #00557f; border: 1px solid #ccc; border-radius: 5px;")

        info_layout = QGridLayout()
        info_layout.setHorizontalSpacing(10)
        info_layout.setVerticalSpacing(5)

        fields_to_add = [
            ('KetQua', 'Kết quả'), ('Mã lệnh', 'Mã lệnh'), ('Tên hàng hoá', 'Tên hàng hoá'),
            ('Phân loại', 'Phân loại'), ('Nhập', 'Nhập'), ('Xuất', 'Xuất'), ('Tên kho chứa', 'Tên kho chứa')
        ]
        for i, (key, text) in enumerate(fields_to_add):
            self._add_info_row(info_layout, key, text, i, 0)
        
        info_layout.setColumnStretch(1, 1)

        content_layout.addWidget(self.camera_view, 1)
        content_layout.addLayout(info_layout)
        content_layout.addStretch()

    def update_camera_frame(self, q_image):
        self.camera_view.setStyleSheet("background-color: black;")
        pixmap = QPixmap.fromImage(q_image)
        self.camera_view.setPixmap(pixmap.scaled(self.camera_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def reset(self):
        super().reset()
        self.camera_view.setText("ĐANG KẾT NỐI CAMERA...")
        self.camera_view.setStyleSheet("color: white; font-weight: bold; font-size: 14pt; background-color: #00557f; border: 1px solid #ccc; border-radius: 5px;")


class Step2_DriverInfoWidget(BaseStepWidget):
    """Bước 2: Hiển thị thông tin lái xe."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 2: THÔNG TIN LÁI XE", parent)
        content_layout = QGridLayout(self.content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        fields_to_add = [
            ('KetQua', 'Kết quả', 0, 0), ('Năm sinh', 'Năm sinh', 0, 1),
            ('Mã lái xe', 'Mã lái xe', 1, 0), ('Đơn vị', 'Đơn vị', 1, 1),
            ('Quản lý', 'Quản lý', 2, 0), ('Trạng thái', 'Trạng thái', 2, 1)
        ]
        for key, text, row, col in fields_to_add:
            self._add_info_row(content_layout, key, text, row, col)
        
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(3, 1)


class Step3_VehicleInfoWidget(BaseStepWidget):
    """Bước 3: Hiển thị thông tin phương tiện."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 3: THÔNG TIN PHƯƠNG TIỆN", parent)
        content_layout = QGridLayout(self.content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)

        fields_to_add = [
            ('KetQua', 'Kết quả', 0, 0), ('Tự trọng xe', 'Tự trọng xe', 0, 1),
            ('Biển số', 'Biển số', 1, 0), ('Tên gọi tắt', 'Tên gọi tắt', 1, 1)
        ]
        for key, text, row, col in fields_to_add:
            self._add_info_row(content_layout, key, text, row, col)
        
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(3, 1)


class Step4_WeightInfoWidget(BaseStepWidget):
    """Bước 4: Hiển thị thông tin phiếu cân."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 4: THÔNG TIN PHIẾU CÂN", parent)
        content_layout = QGridLayout(self.content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)

        fields_to_add = [
            ('Phiếu cân', 'PHIẾU CÂN', 0, 0), ('TRANGTHAI', 'TRẠNG THÁI', 0, 1),
            ('Cân lần 1 (Kg)', 'Cân lần 1 (Kg)', 1, 0), ('Thời gian cân lần 1', 'Thời gian cân lần 1', 1, 1),
            ('Cân lần 2 (Kg)', 'Cân lần 2 (Kg)', 2, 0), ('Thời gian cân lần 2', 'Thời gian cân lần 2', 2, 1),
            ('Hàng hoá (Kg)', 'Hàng hoá (Kg)', 3, 0),
            ('Độ lệch bì (Kg)', 'Độ lệch bì (Kg)', 4, 0)
        ]
        for key, text, row, col in fields_to_add:
            self._add_info_row(content_layout, key, text, row, col)
        
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(3, 1)
