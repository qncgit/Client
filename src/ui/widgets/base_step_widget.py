from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

class BaseStepWidget(QFrame):
    """
    Lớp cơ sở cho các widget hiển thị thông tin theo từng bước.
    Cung cấp một cấu trúc chung và phương thức reset.
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(7)

        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(12)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #00557f; background-color: #cce7ff; padding: 5px; border-radius: 5px;")
        
        self.main_layout.addWidget(self.title_label)
        
        self.info_labels = {}

    def _add_info_row(self, key, label_text):
        """Thêm một hàng thông tin (gồm nhãn và giá trị)."""
        row_layout = QVBoxLayout()
        row_layout.setSpacing(2)  # Giảm khoảng cách giữa các dòng
        
        label = QLabel(f"{label_text}:")
        label.setStyleSheet("font-weight: bold; color: #333; padding: 0px 2px;")
        label.setMinimumHeight(18)
        label.setMaximumHeight(22)
        
        value_label = QLabel("...")
        value_label.setStyleSheet("font-size: 11pt; color: #000; padding: 0px 2px;")
        value_label.setWordWrap(True)
        value_label.setMinimumHeight(18)   # Giảm chiều cao tối thiểu
        value_label.setMaximumHeight(24)   # Giảm chiều cao tối đa

        row_layout.addWidget(label)
        row_layout.addWidget(value_label)
        
        self.main_layout.addLayout(row_layout)
        self.info_labels[key] = value_label

    def update_info(self, data_dict):
        """Cập nhật thông tin cho các label từ một dictionary."""
        if not data_dict:
            self.reset()
            return

        for key, label in self.info_labels.items():
            value = data_dict.get(key, 'N/A')
            label.setText(str(value))

    def update_font_size(self, font_size):
        """
        Cập nhật cỡ chữ động cho title và các label thông tin.
        """
        # Title label
        f = self.title_label.font()
        f.setPointSize(font_size + 2)
        self.title_label.setFont(f)
        self.title_label.setStyleSheet("color: #00557f; background-color: #cce7ff; padding: 5px; border-radius: 5px;")
        # Info labels
        for value_label in self.info_labels.values():
            value_label.setStyleSheet(f"font-size: {font_size}pt; color: #000; padding: 0px 2px;")
            value_label.setMinimumHeight(max(16, font_size + 2))
            value_label.setMaximumHeight(max(20, font_size + 6))

    def reset(self):
        """Reset tất cả các label giá trị về trạng thái ban đầu."""
        for label in self.info_labels.values():
            label.setText("...")

