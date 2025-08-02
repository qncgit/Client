# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/widgets/header_widget.py
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGridLayout, QLabel
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
# Import các widget chuyên dụng từ thư viện fluent
from qfluentwidgets import CardWidget, TitleLabel, SubtitleLabel, FluentIcon as FIF, BodyLabel, IconWidget

class HeaderWidget(QWidget):
    """
    Widget phần Header, được viết lại bằng qfluentwidgets.
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
        layout.setSpacing(10)

        # Phần khối lượng cân (bên trái) được gói trong CardWidget
        weight_card = CardWidget()
        weight_layout = QHBoxLayout(weight_card)
        
        self.weight_label = TitleLabel("0")
        self.weight_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.weight_label.setStyleSheet("color: #d32f2f;")
        
        unit_label = SubtitleLabel("KG")
        unit_label.setFont(QFont("Arial", 24, QFont.Bold))

        weight_layout.addStretch()
        weight_layout.addWidget(self.weight_label, 0, Qt.AlignRight)
        weight_layout.addWidget(unit_label, 0, Qt.AlignBottom)
        weight_layout.addStretch()
        
        # Phần thông tin (bên phải) cũng được gói trong CardWidget
        info_card = CardWidget()
        info_layout = QGridLayout(info_card)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(20, 15, 20, 15)

        self.time_label = BodyLabel("-")
        self.station_label = BodyLabel("-")
        self.mode_label = BodyLabel("-")
        
        # Thêm biểu tượng trạng thái mạng
        self.network_status = IconWidget(FIF.LINK)
        self.network_status.setToolTip("Đang kết nối trực tuyến")
        self.network_status.setStyleSheet("color: #107C10;")  # Xanh lá
        
        # Sử dụng các label chuyên dụng cho tiêu đề và nội dung
        info_layout.addWidget(SubtitleLabel("Thời gian:"), 0, 0, alignment=Qt.AlignRight)
        info_layout.addWidget(self.time_label, 0, 1, alignment=Qt.AlignRight)
        info_layout.addWidget(SubtitleLabel("Trạm cân:"), 1, 0, alignment=Qt.AlignRight)
        info_layout.addWidget(self.station_label, 1, 1, alignment=Qt.AlignRight)
        info_layout.addWidget(SubtitleLabel("Kiểu cân:"), 2, 0, alignment=Qt.AlignRight)
        info_layout.addWidget(self.mode_label, 2, 1, alignment=Qt.AlignRight)
        info_layout.addWidget(self.network_status, 3, 0, 1, 2, alignment=Qt.AlignCenter)
        info_layout.setColumnStretch(1, 1)

        layout.addWidget(weight_card, 4)
        layout.addWidget(info_card, 1)

        # Create offline status layout
        self.offline_layout = QHBoxLayout()
        
        # Create offline status label with orange background and white text
        self.offline_status = QLabel("Trạng thái: -")
        self.offline_status.setStyleSheet("""
            background-color: #FF8C00; 
            color: white; 
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        
        # Create offline count label
        self.offline_count = QLabel("0")
        self.offline_count.setStyleSheet("""
            background-color: #FF5722;
            color: white;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
            margin-left: 5px;
        """)
        
        # Add widgets to layout
        self.offline_layout.addWidget(self.offline_status)
        self.offline_layout.addWidget(self.offline_count)
        self.offline_layout.addStretch(1)
        
        layout.addLayout(self.offline_layout)

        # Ẩn các phần tử trạng thái offline ban đầu
        self.offline_status.setVisible(False)
        self.offline_count.setVisible(False)

        self.reload_config()
    
    def update_weight(self, weight_value):
        self.weight_label.setText(f"{weight_value:,}".replace(",", "."))

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.time_label.setText(current_time.toString('dd/MM/yyyy hh:mm:ss'))

    def update_mode(self, mode_text):
        self.mode_label.setText(mode_text)

    def reload_config(self):
        station_name = self._config.get('location_label.name', 'TRẠM CÂN')
        self.station_label.setText(station_name)
        
        mode_desc = self._config.get(f'scale_mode.description', 'Chưa rõ')
        self.update_mode(mode_desc)

    def update_network_status(self, is_online):
        """Cập nhật trạng thái kết nối mạng"""
        if is_online:
            self.network_status.setIcon(FIF.LINK)
            self.network_status.setToolTip("Đang kết nối trực tuyến")
            self.network_status.setStyleSheet("color: #107C10;")  # Xanh lá
            self.offline_status.setText("Trạng thái: Đang kết nối trực tuyến")
            self.offline_status.setStyleSheet("""
                background-color: #107C10; 
                color: white; 
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 4px;
            """)
            
            # Hiển thị số phiếu offline nếu có
            count = int(self.offline_count.text() or "0")
            if count > 0:
                self.offline_count.setVisible(True)
                self.offline_status.setVisible(True)  # Hiển thị khi có phiếu đang chờ đồng bộ
            else:
                self.offline_count.setVisible(False)
                self.offline_status.setVisible(False)  # Ẩn khi không có phiếu chờ
        else:
            self.network_status.setIcon(FIF.CANCEL)
            self.network_status.setToolTip("Đang làm việc ngoại tuyến")
            self.network_status.setStyleSheet("color: #E74856;")  # Đỏ
            self.offline_status.setText("Trạng thái: Đang trong chế độ offline")
            self.offline_status.setStyleSheet("""
                background-color: #FF8C00; 
                color: white; 
                font-weight: bold;
                padding: 3px 8px;
                border-radius: 4px;
            """)
            self.offline_status.setVisible(True)  # Luôn hiển thị khi offline
            self.offline_count.setVisible(False)

    def update_offline_count(self, count):
        """Cập nhật số phiếu cân đang chờ đồng bộ"""
        self.offline_count.setText(str(count))
        if count > 0:
            self.offline_status.setVisible(True)
            self.offline_count.setVisible(True)
        else:
            self.offline_status.setVisible(False)
            self.offline_count.setVisible(False)