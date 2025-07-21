import sys
import copy
from PyQt5.QtWidgets import QApplication, QWidget, QFormLayout, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from qfluentwidgets import (setTheme, Theme, FluentWindow, SubtitleLabel, NavigationInterface,
                            NavigationItemPosition, MessageBox, LineEdit, SpinBox, ComboBox,
                            SwitchButton, PushButton, PrimaryPushButton, CardWidget, SplitTitleBar)
from src.utils.helpers import Common

class SettingDialog(FluentWindow):
    """
    Cửa sổ cài đặt được viết lại bằng thư viện PyQt-Fluent-Widgets.
    """
    # SỬA LỖI: Thêm tín hiệu để thông báo cho cửa sổ chính khi lưu thành công
    settings_saved = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        
        self.titleBar.setAttribute(Qt.WA_StyledBackground)
        
        self.setWindowTitle("Cài đặt hệ thống")
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        
        # --- Tạo các trang cài đặt ---
        self.serverPage = QWidget()
        self.comPage = QWidget()
        self.cameraPage = QWidget()
        self.generalPage = QWidget()
        
        self.serverPage.setObjectName('serverPage')
        self.comPage.setObjectName('comPage')
        self.cameraPage.setObjectName('cameraPage')
        self.generalPage.setObjectName('generalPage')
        
        self._setup_server_ui()
        self._setup_com_ui()
        self._setup_camera_ui()
        self._setup_general_ui()
        
        self._init_navigation()
        self.resize(800, 600)
        
        self._load_settings()

    def _init_navigation(self):
        self.addSubInterface(self.serverPage, ':/qfluentwidgets/images/navigation/Web.png', 'Máy chủ & API')
        self.addSubInterface(self.comPage, ':/qfluentwidgets/images/navigation/Sending.png', 'Cổng COM (Cân)')
        self.addSubInterface(self.cameraPage, ':/qfluentwidgets/images/navigation/Camera.png', 'Camera')
        self.addSubInterface(self.generalPage, ':/qfluentwidgets/images/navigation/Settings.png', 'Cài đặt chung')
        
        # Nút Lưu và Hủy
        self.saveButton = PrimaryPushButton("Lưu cài đặt")
        self.cancelButton = PushButton("Hủy")
        self.saveButton.clicked.connect(self.on_save)
        self.cancelButton.clicked.connect(self.close)
        
        self.navigationInterface.addWidget(
            routeKey='save',
            widget=self.saveButton,
            position=NavigationItemPosition.BOTTOM
        )
        self.navigationInterface.addWidget(
            routeKey='cancel',
            widget=self.cancelButton,
            position=NavigationItemPosition.BOTTOM
        )

    def _setup_server_ui(self):
        layout = QFormLayout(self.serverPage)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        self.host_input = LineEdit()
        self.port_input = SpinBox()
        self.port_input.setRange(1, 65535)
        self.token_input = LineEdit()
        self.project_id_input = LineEdit()
        self.table_id_phieu_can_input = LineEdit()
        self.table_id_lenh_can_input = LineEdit()
        self.view_id_lenh_can_input = LineEdit()
        self.table_id_phuong_tien_input = LineEdit()
        self.view_id_phuong_tien_input = LineEdit()
        self.table_id_nhan_vien_input = LineEdit()
        self.view_id_nhan_vien_input = LineEdit()

        layout.addRow(SubtitleLabel("Kết nối máy chủ"))
        layout.addRow("Host/IP Máy chủ:", self.host_input)
        layout.addRow("Port:", self.port_input)
        layout.addRow("API Token (xc-token):", self.token_input)
        
        layout.addRow(SubtitleLabel("NocoDB API"))
        layout.addRow("Project ID:", self.project_id_input)
        layout.addRow("Table ID (Lịch sử cân):", self.table_id_phieu_can_input)
        layout.addRow("Table ID (Lệnh cân):", self.table_id_lenh_can_input)
        layout.addRow("View ID (Lệnh cân):", self.view_id_lenh_can_input)
        layout.addRow("Table ID (Phương tiện):", self.table_id_phuong_tien_input)
        layout.addRow("View ID (Phương tiện):", self.view_id_phuong_tien_input)
        layout.addRow("Table ID (Nhân viên):", self.table_id_nhan_vien_input)
        layout.addRow("View ID (Nhân viên):", self.view_id_nhan_vien_input)

    def _setup_com_ui(self):
        layout = QFormLayout(self.comPage)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        self.com_port_input = LineEdit()
        self.com_baudrate_input = ComboBox()
        self.com_baudrate_input.addItems(['4800', '9600', '19200', '38400', '57600', '115200'])
        self.com_bytesize_input = ComboBox()
        self.com_bytesize_input.addItems(['5', '6', '7', '8'])
        self.com_parity_input = ComboBox()
        self.com_parity_input.addItems(['N', 'E', 'O'])
        self.com_stopbits_input = ComboBox()
        self.com_stopbits_input.addItems(['1', '1.5', '2'])
        self.com_timeout_input = SpinBox()
        self.com_timeout_input.setRange(0, 10)

        layout.addRow("Cổng COM (vd: COM1):", self.com_port_input)
        layout.addRow("Baudrate:", self.com_baudrate_input)
        layout.addRow("Bytesize:", self.com_bytesize_input)
        layout.addRow("Parity (N-None, E-Even, O-Odd):", self.com_parity_input)
        layout.addRow("Stop bits:", self.com_stopbits_input)
        layout.addRow("Timeout (giây):", self.com_timeout_input)

    def _setup_camera_ui(self):
        layout = QFormLayout(self.cameraPage)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        self.use_webcam_switch = SwitchButton("Sử dụng Webcam")
        self.webcam_index_input = SpinBox()
        self.rtsp_url_input = LineEdit()
        
        self.use_webcam_switch.checkedChanged.connect(self._toggle_camera_inputs)

        layout.addRow(self.use_webcam_switch)
        layout.addRow("Chỉ số Webcam:", self.webcam_index_input)
        layout.addRow("URL RTSP:", self.rtsp_url_input)
        
    def _toggle_camera_inputs(self, checked):
        self.webcam_index_input.setEnabled(checked)
        self.rtsp_url_input.setEnabled(not checked)

    def _setup_general_ui(self):
        layout = QVBoxLayout(self.generalPage)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        general_card = CardWidget()
        general_layout = QFormLayout(general_card)
        self.station_name_input = LineEdit()
        self.mode_input = ComboBox()
        self.mode_input.addItems(['auto', 'in', 'out'])
        self.reset_time_input = SpinBox()
        self.reset_time_input.setRange(5, 300)
        self.sync_time_input = SpinBox()
        self.sync_time_input.setRange(10, 600)
        general_layout.addRow(SubtitleLabel("Cài đặt chung"))
        general_layout.addRow("Tên trạm cân:", self.station_name_input)
        general_layout.addRow("Chế độ cân:", self.mode_input)
        general_layout.addRow("Thời gian tự reset (giây):", self.reset_time_input)
        general_layout.addRow("Chu kỳ đồng bộ dữ liệu (giây):", self.sync_time_input)
        
        password_card = CardWidget()
        password_layout = QFormLayout(password_card)
        self.new_password_input = LineEdit()
        self.new_password_input.setEchoMode(LineEdit.Password)
        self.confirm_password_input = LineEdit()
        self.confirm_password_input.setEchoMode(LineEdit.Password)
        password_layout.addRow(SubtitleLabel("Thay đổi mật khẩu quản trị"))
        password_layout.addRow("Mật khẩu mới:", self.new_password_input)
        password_layout.addRow("Xác nhận mật khẩu:", self.confirm_password_input)

        layout.addWidget(general_card)
        layout.addWidget(password_card)
        layout.addStretch()

    def _load_settings(self):
        # Server
        self.host_input.setText(self._config.get('server.host', ''))
        self.port_input.setValue(self._config.get('server.port', 8080))
        self.token_input.setText(self._config.get('server.api_token', ''))
        
        # NocoDB
        self.project_id_input.setText(self._config.get('nocodb.base.id', ''))
        
        nv_table = self._config.get_nocodb_table_by_name("Thông tin nhân viên")
        if nv_table:
            self.table_id_nhan_vien_input.setText(nv_table.get('id', ''))
            nv_view = self._config.get_nocodb_view_by_name(nv_table, "Thongtinnhanvien")
            if nv_view: self.view_id_nhan_vien_input.setText(nv_view.get('id', ''))

        pt_table = self._config.get_nocodb_table_by_name("Thông tin phương tiện")
        if pt_table:
            self.table_id_phuong_tien_input.setText(pt_table.get('id', ''))
            pt_view = self._config.get_nocodb_view_by_name(pt_table, "Thongtinphuongtien")
            if pt_view: self.view_id_phuong_tien_input.setText(pt_view.get('id', ''))

        lc_table = self._config.get_nocodb_table_by_name("Thông tin lệnh cân")
        if lc_table:
            self.table_id_lenh_can_input.setText(lc_table.get('id', ''))
            lc_view = self._config.get_nocodb_view_by_name(lc_table, "Thongtinlenhcan")
            if lc_view: self.view_id_lenh_can_input.setText(lc_view.get('id', ''))

        pc_table = self._config.get_nocodb_table_by_name("Lịch sử cân")
        if pc_table: self.table_id_phieu_can_input.setText(pc_table.get('id', ''))

        # COM
        self.com_port_input.setText(self._config.get('scale.com_port', 'COM1'))
        self.com_baudrate_input.setText(str(self._config.get('scale.baud_rate', 9600)))
        self.com_bytesize_input.setText(str(self._config.get('scale.bytesize', 8)))
        self.com_parity_input.setText(self._config.get('scale.parity', 'N'))
        self.com_stopbits_input.setText(str(self._config.get('scale.stop_bits', 1)))
        self.com_timeout_input.setValue(self._config.get('scale.timeout', 1))

        # Camera
        cam_type = self._config.get('camera.qr.type', 'webcam')
        use_webcam = (cam_type == 'webcam')
        self.use_webcam_switch.setChecked(use_webcam)
        self.webcam_index_input.setValue(self._config.get('camera.qr.webcam.index', 0))
        self.rtsp_url_input.setText(self._config.get('camera.qr.rtsp.url', ''))
        self._toggle_camera_inputs(use_webcam)

        # General
        self.station_name_input.setText(self._config.get('location_label.name', 'TRẠM CÂN'))
        self.mode_input.setText(self._config.get('scale_mode.type', 'auto'))
        self.reset_time_input.setValue(self._config.get('reset_time', 15))
        self.sync_time_input.setValue(self._config.get('server.sync_interval', 60))

    def on_save(self):
        new_config = copy.deepcopy(self._config.config)

        # Cập nhật tất cả các trường...
        new_config['server']['host'] = self.host_input.text()
        new_config['server']['port'] = self.port_input.value()
        new_config['server']['api_token'] = self.token_input.text()
        new_config['server']['sync_interval'] = self.sync_time_input.value()
        new_config['nocodb']['base']['id'] = self.project_id_input.text()
        
        def update_nocodb_ids(table_name, view_name, table_id_widget, view_id_widget=None):
            tables = new_config['nocodb']['tables']
            for key, table in tables.items():
                if table.get('name') == table_name:
                    table['id'] = table_id_widget.text()
                    if view_id_widget:
                        for v_key, view in table.get('views', {}).items():
                            if view.get('name') == view_name:
                                view['id'] = view_id_widget.text()
                                break
                    break
        
        update_nocodb_ids("Thông tin nhân viên", "Thongtinnhanvien", self.table_id_nhan_vien_input, self.view_id_nhan_vien_input)
        update_nocodb_ids("Thông tin phương tiện", "Thongtinphuongtien", self.table_id_phuong_tien_input, self.view_id_phuong_tien_input)
        update_nocodb_ids("Thông tin lệnh cân", "Thongtinlenhcan", self.table_id_lenh_can_input, self.view_id_lenh_can_input)
        update_nocodb_ids("Lịch sử cân", None, self.table_id_phieu_can_input)

        new_config['scale']['com_port'] = self.com_port_input.text()
        new_config['scale']['baud_rate'] = int(self.com_baudrate_input.text())
        new_config['scale']['bytesize'] = int(self.com_bytesize_input.text())
        new_config['scale']['parity'] = self.com_parity_input.text()
        new_config['scale']['stop_bits'] = float(self.com_stopbits_input.text())
        new_config['scale']['timeout'] = self.com_timeout_input.value()

        new_config['camera']['qr']['type'] = 'webcam' if self.use_webcam_switch.isChecked() else 'rtsp'
        new_config['camera']['qr']['webcam']['index'] = self.webcam_index_input.value()
        new_config['camera']['qr']['rtsp']['url'] = self.rtsp_url_input.text()

        new_config['location_label']['name'] = self.station_name_input.text()
        new_config['scale_mode']['type'] = self.mode_input.text()
        new_config['reset_time'] = self.reset_time_input.value()
        
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()
        if new_pass:
            if new_pass != confirm_pass:
                m = MessageBox('Lỗi', 'Mật khẩu mới và mật khẩu xác nhận không khớp!', self)
                m.exec()
                return
            new_config['admin']['password_hash'] = Common.hash_password(new_pass)

        self._config.set_all(new_config)
        if self._config.save_config():
            # SỬA LỖI: Phát tín hiệu và đóng cửa sổ
            self.settings_saved.emit()
            m = MessageBox('Thành công', 'Đã lưu cài đặt!', self)
            m.exec()
            self.close()
        else:
            m = MessageBox('Lỗi', 'Không thể lưu file cấu hình!', self)
            m.exec()
