from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QGridLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class HeaderWidget(QWidget):
    """
    Widget phần Header, được viết lại để khớp với thiết kế gốc.
    """
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self._config = config_manager
        self.init_ui()
        self.update_time()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Phần khối lượng cân (bên trái)
        weight_container = QFrame()
        weight_container.setStyleSheet("background-color: white; border-radius: 8px;")
        weight_layout = QHBoxLayout(weight_container)

        self.weight_label = QLabel("0")
        font = QFont("Arial", 72, QFont.Bold)
        self.weight_label.setFont(font)
        self.weight_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.weight_label.setStyleSheet("color: #d32f2f; background-color: transparent;")

        unit_label = QLabel("KG")
        font = QFont("Arial", 24, QFont.Bold)
        unit_label.setFont(font)
        unit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        unit_label.setStyleSheet("color: #333; padding-left: 10px; background-color: transparent;")

        weight_layout.addStretch()
        weight_layout.addWidget(self.weight_label)
        weight_layout.addWidget(unit_label)
        weight_layout.addStretch()

        # Phần thông tin (bên phải)
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(10, 10, 10, 10)

        self.time_label = QLabel("-")
        self.station_label = QLabel("-")
        self.mode_label = QLabel("-")

        for label in [self.time_label, self.station_label, self.mode_label]:
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setStyleSheet("font-size: 11pt; color: #000; font-weight: bold;")

        info_layout.addWidget(self._create_title_label("Thời gian:"), 0, 0)
        info_layout.addWidget(self.time_label, 0, 1)
        info_layout.addWidget(self._create_title_label("Trạm cân:"), 1, 0)
        info_layout.addWidget(self.station_label, 1, 1)
        info_layout.addWidget(self._create_title_label("Kiểu cân:"), 2, 0)
        info_layout.addWidget(self.mode_label, 2, 1)
        info_layout.setColumnStretch(1, 1)

        layout.addWidget(weight_container, 1)
        layout.addLayout(info_layout, 1)

        self.reload_config()

    def _create_title_label(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #555;")
        return label

    def update_weight(self, weight_value):
        self.weight_label.setText(f"{weight_value:,}".replace(",", "."))

    def update_time(self):
        from PyQt5.QtCore import QDateTime
        current_time = QDateTime.currentDateTime()
        self.time_label.setText(current_time.toString('dd/MM/yyyy hh:mm:ss'))

    def update_mode(self, mode_text):
        self.mode_label.setText(mode_text)

    def reload_config(self):
        self.station_label.setText(self._config.get('station_name', 'TRẠM CÂN'))
        mode_map = {'auto': 'Tự Động', 'in': 'Cân Vào', 'out': 'Cân Ra'}
        self.mode_label.setText(mode_map.get(self._config.get('mode', 'auto')))
