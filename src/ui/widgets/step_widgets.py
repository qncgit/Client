# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/widgets/step_widgets.py
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QGridLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
# Import các widget từ thư viện fluent
from qfluentwidgets import CardWidget, TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel

class BaseStepWidget(CardWidget):
    """
    Lớp cơ sở cho các widget hiển thị thông tin, viết lại bằng CardWidget.
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.title_label = TitleLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setProperty('level', 'h2')
        self.title_label.setStyleSheet("background-color: #00557f; color: white; padding: 8px; border-top-left-radius: 8px; border-top-right-radius: 8px;")

        self.content_container = QWidget()
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.content_container, 1)

        self.info_fields = {}

    def _add_info_row(self, layout, key, label_text, row, col):
        """Thêm một hàng thông tin vào layout dạng lưới."""
        label = StrongBodyLabel(f"{label_text}:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        value_field = BodyLabel("-")
        value_field.setWordWrap(True)
        value_field.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f9f9f9;")
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
            text = str(value) if value is not None else '-'
            field.setText(text)
            # Giảm size chữ nếu dữ liệu quá dài
            default_font = field.font()
            default_size = default_font.pointSize()
            # Nếu text dài hơn 40 ký tự thì giảm font size
            if len(text) > 40:
                new_size = max(10, default_size - 2)
                f = field.font()
                f.setPointSize(new_size)
                field.setFont(f)
            else:
                f = field.font()
                f.setPointSize(default_size)
                field.setFont(f)

    def reset(self):
        for field in self.info_fields.values():
            field.setText("-")
            # Reset font size về mặc định
            f = field.font()
            f.setPointSize(12)
            field.setFont(f)

    def update_font_size(self, font_size):
        f = self.title_label.font()
        f.setPointSize(font_size + 2)
        self.title_label.setFont(f)
        for field in self.info_fields.values():
            f = field.font()
            f.setPointSize(font_size)
            field.setFont(f)
            field.setMinimumHeight(max(18, font_size + 2))
            field.setMaximumHeight(max(46, font_size + 6))
        for layout in self.content_container.findChildren(QGridLayout):
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, StrongBodyLabel):
                    f = widget.font()
                    f.setPointSize(font_size)
                    widget.setFont(f)


class Step1_QRScanWidget(BaseStepWidget):
    def __init__(self, parent=None):
        super().__init__("BƯỚC 1: THÔNG TIN LỆNH VẬN CHUYỂN (QUÉT QR)", parent)

        content_layout = QVBoxLayout(self.content_container)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(15, 15, 15, 15)

        self.camera_view = QLabel("ĐANG KẾT NỐI CAMERA...")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setMinimumSize(320, 240)
        self.camera_view.setStyleSheet("color: white; font-weight: bold; font-size: 14pt; background-color: black; border-radius: 5px;")

        info_layout = QGridLayout()
        info_layout.setHorizontalSpacing(10)
        info_layout.setVerticalSpacing(8)

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

        # Biến để kiểm soát việc khoá hình ảnh QR
        self.is_qr_locked = False
        self.last_qr_frame = None

    def update_camera_frame(self, q_image):
        """Cập nhật frame từ camera"""
        if self.is_qr_locked:
            # Nếu đang khoá QR, hiển thị frame đã lưu
            if self.last_qr_frame:
                self.camera_view.setPixmap(self.last_qr_frame)
        else:
            # Nếu không khoá, hiển thị frame mới
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.camera_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.camera_view.setPixmap(scaled_pixmap)

    def lock_qr_frame(self):
        """Khoá frame QR hiện tại"""
        self.is_qr_locked = True
        if self.camera_view.pixmap():
            self.last_qr_frame = self.camera_view.pixmap()
            
    def unlock_qr_frame(self):
        """Mở khoá frame QR"""
        self.is_qr_locked = False
        self.last_qr_frame = None
        # Không có thêm thao tác nào khác ở đây để đảm bảo timer tiếp tục chạy

    def reset(self):
        super().reset()
        self.unlock_qr_frame()
        self.camera_view.setText("ĐANG CHỜ...")
        self.camera_view.setStyleSheet("color: white; font-weight: bold; font-size: 14pt; background-color: black; border-radius: 5px;")

    def reset_data(self):
        """Reset chỉ dữ liệu, không reset trạng thái camera"""
        for field in self.info_fields.values():
            field.setText("-")
            # Reset font size về mặc định
            f = field.font()
            f.setPointSize(12)
            field.setFont(f)
        # Luôn unlock QR frame khi reset data
        self.unlock_qr_frame()


class Step2_DriverInfoWidget(BaseStepWidget):
    """Bước 2: Hiển thị thông tin lái xe."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 2: THÔNG TIN LÁI XE", parent)
        content_layout = QGridLayout(self.content_container)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
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
        content_layout = QGridLayout(self.content_container)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(15, 15, 15, 15)

        fields_to_add = [
            ('KetQua', 'Kết quả', 0, 0), ('Tự trọng xe', 'Tự trọng', 0, 1),
            ('Biển số', 'Biển số', 1, 0), ('Tên gọi tắt', 'Tên gọi tắt', 1, 1)
        ]
        for key, text, row, col in fields_to_add:
            self._add_info_row(content_layout, key, text, row, col)
        
        self.info_fields['Tự trọng xe'].setText("- Kg")
        
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(3, 1)
    
    def update_info(self, data_dict):
        super().update_info(data_dict)
        tu_trong = data_dict.get('Tự trọng xe', '-')
        tu_trong_text = f"{int(tu_trong):,} Kg".replace(",",".") if isinstance(tu_trong, (int, float)) else "- Kg"
        self.info_fields['Tự trọng xe'].setText(tu_trong_text)


class Step4_WeightInfoWidget(BaseStepWidget):
    """Bước 4: Hiển thị thông tin phiếu cân."""
    def __init__(self, parent=None):
        super().__init__("BƯỚC 4: THÔNG TIN PHIẾU CÂN", parent)
        content_layout = QGridLayout(self.content_container)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(15, 15, 15, 15)

        # Phiếu cân chiếm toàn bộ dòng 0 (4 cột)
        self._add_info_row(content_layout, 'Phiếu cân', 'PHIẾU CÂN', 0, 0)
        content_layout.addWidget(self.info_fields['Phiếu cân'], 0, 1, 1, 3)

        # Trạng thái chiếm toàn bộ dòng 1 (4 cột)
        self._add_info_row(content_layout, 'TRANGTHAI', 'TRẠNG THÁI', 1, 0)
        content_layout.addWidget(self.info_fields['TRANGTHAI'], 1, 1, 1, 3)

        # Cân lần 1 và TG Cân 1 cùng dòng, thẳng hàng, có khung vuông
        label_can1 = StrongBodyLabel("Cân lần 1:")
        label_can1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        content_layout.addWidget(label_can1, 2, 0)
        self.info_fields['Cân lần 1 (Kg)'] = BodyLabel("-")
        self.info_fields['Cân lần 1 (Kg)'].setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f9f9f9;"
        )
        self.info_fields['Cân lần 1 (Kg)'].setMinimumHeight(28)
        content_layout.addWidget(self.info_fields['Cân lần 1 (Kg)'], 2, 1)

        label_tg1 = StrongBodyLabel("TG Cân 1:")
        label_tg1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        content_layout.addWidget(label_tg1, 2, 2)
        self.info_fields['Thời gian cân lần 1'] = BodyLabel("-")
        self.info_fields['Thời gian cân lần 1'].setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f9f9f9;"
        )
        self.info_fields['Thời gian cân lần 1'].setMinimumHeight(28)
        content_layout.addWidget(self.info_fields['Thời gian cân lần 1'], 2, 3)

        # Cân lần 2 và TG Cân 2 cùng dòng, thẳng hàng, có khung vuông
        label_can2 = StrongBodyLabel("Cân lần 2:")
        label_can2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        content_layout.addWidget(label_can2, 3, 0)
        self.info_fields['Cân lần 2 (Kg)'] = BodyLabel("-")
        self.info_fields['Cân lần 2 (Kg)'].setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f9f9f9;"
        )
        self.info_fields['Cân lần 2 (Kg)'].setMinimumHeight(28)
        content_layout.addWidget(self.info_fields['Cân lần 2 (Kg)'], 3, 1)

        label_tg2 = StrongBodyLabel("TG Cân 2:")
        label_tg2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        content_layout.addWidget(label_tg2, 3, 2)
        self.info_fields['Thời gian cân lần 2'] = BodyLabel("-")
        self.info_fields['Thời gian cân lần 2'].setStyleSheet(
            "border: 1px solid #ccc; border-radius: 4px; padding: 4px; background-color: #f9f9f9;"
        )
        self.info_fields['Thời gian cân lần 2'].setMinimumHeight(28)
        content_layout.addWidget(self.info_fields['Thời gian cân lần 2'], 3, 3)

        # Các trường còn lại
        self._add_info_row(content_layout, 'Hàng hoá (Kg)', 'Hàng hoá', 4, 0)
        content_layout.addWidget(self.info_fields['Hàng hoá (Kg)'], 4, 1, 1, 3)
        self._add_info_row(content_layout, 'Độ lệch bì (Kg)', 'Độ lệch bì', 5, 0)
        content_layout.addWidget(self.info_fields['Độ lệch bì (Kg)'], 5, 1, 1, 3)

        # Căn cột cho layout
        content_layout.setColumnStretch(1, 1)
        content_layout.setColumnStretch(2, 1)
        content_layout.setColumnStretch(3, 1)