from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, 
                             QLineEdit, QPushButton, QDialogButtonBox, QSpinBox, 
                             QComboBox, QCheckBox, QMessageBox, QGroupBox)
# SỬA LỖI: Xóa import không cần thiết
# from .verified_dialog import VerifiedDialog 
from src.utils.helpers import hash_password
import copy

class SettingDialog(QDialog):
    """
    Cửa sổ cài đặt cho phép người dùng cấu hình toàn bộ hệ thống,
    tương thích với cấu trúc config.json mới.
    """
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self.setWindowTitle("Cài đặt hệ thống")
        self.setMinimumSize(600, 500)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tabs.addTab(self._create_server_tab(), "Máy chủ & API")
        self.tabs.addTab(self._create_com_tab(), "Cổng COM (Cân)")
        self.tabs.addTab(self._create_camera_tab(), "Camera")
        self.tabs.addTab(self._create_general_tab(), "Cài đặt chung")

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        main_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

        self._load_settings()

    def _create_server_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.host_input = QLineEdit()
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.token_input = QLineEdit()
        self.project_id_input = QLineEdit()
        self.table_id_phieu_can_input = QLineEdit()
        self.table_id_lenh_can_input = QLineEdit()
        self.view_id_lenh_can_input = QLineEdit()
        self.table_id_phuong_tien_input = QLineEdit()
        self.view_id_phuong_tien_input = QLineEdit()
        self.table_id_nhan_vien_input = QLineEdit()
        self.view_id_nhan_vien_input = QLineEdit()

        layout.addRow("Host/IP Máy chủ:", self.host_input)
        layout.addRow("Port:", self.port_input)
        layout.addRow("API Token (xc-token):", self.token_input)
        layout.addRow("Project ID:", self.project_id_input)
        layout.addRow("Table ID (Lịch sử cân):", self.table_id_phieu_can_input)
        layout.addRow("Table ID (Lệnh cân):", self.table_id_lenh_can_input)
        layout.addRow("View ID (Lệnh cân):", self.view_id_lenh_can_input)
        layout.addRow("Table ID (Phương tiện):", self.table_id_phuong_tien_input)
        layout.addRow("View ID (Phương tiện):", self.view_id_phuong_tien_input)
        layout.addRow("Table ID (Nhân viên):", self.table_id_nhan_vien_input)
        layout.addRow("View ID (Nhân viên):", self.view_id_nhan_vien_input)
        
        return widget

    def _create_com_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.com_port_input = QLineEdit()
        self.com_baudrate_input = QComboBox()
        self.com_baudrate_input.addItems(['4800', '9600', '19200', '38400', '57600', '115200'])
        self.com_bytesize_input = QComboBox()
        self.com_bytesize_input.addItems(['5', '6', '7', '8'])
        self.com_parity_input = QComboBox()
        self.com_parity_input.addItems(['N', 'E', 'O'])
        self.com_stopbits_input = QComboBox()
        self.com_stopbits_input.addItems(['1', '1.5', '2'])
        self.com_timeout_input = QSpinBox()
        self.com_timeout_input.setRange(0, 10)


        layout.addRow("Cổng COM (vd: COM1):", self.com_port_input)
        layout.addRow("Baudrate:", self.com_baudrate_input)
        layout.addRow("Bytesize:", self.com_bytesize_input)
        layout.addRow("Parity (N-None, E-Even, O-Odd):", self.com_parity_input)
        layout.addRow("Stop bits:", self.com_stopbits_input)
        layout.addRow("Timeout (giây):", self.com_timeout_input)

        return widget

    def _create_camera_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.use_webcam_checkbox = QCheckBox("Sử dụng Webcam")
        self.webcam_index_input = QSpinBox()
        self.rtsp_url_input = QLineEdit()
        
        self.use_webcam_checkbox.toggled.connect(self._toggle_camera_inputs)

        layout.addRow(self.use_webcam_checkbox)
        layout.addRow("Chỉ số Webcam:", self.webcam_index_input)
        layout.addRow("URL RTSP:", self.rtsp_url_input)
        
        return widget
        
    def _toggle_camera_inputs(self, checked):
        self.webcam_index_input.setEnabled(checked)
        self.rtsp_url_input.setEnabled(not checked)

    def _create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        general_group = QGroupBox("Cài đặt chung")
        general_layout = QFormLayout(general_group)
        self.station_name_input = QLineEdit()
        self.mode_input = QComboBox()
        self.mode_input.addItems(['auto', 'in', 'out'])
        self.reset_time_input = QSpinBox()
        self.reset_time_input.setRange(5, 300)
        self.sync_time_input = QSpinBox()
        self.sync_time_input.setRange(10, 600)
        general_layout.addRow("Tên trạm cân:", self.station_name_input)
        general_layout.addRow("Chế độ cân:", self.mode_input)
        general_layout.addRow("Thời gian tự reset (giây):", self.reset_time_input)
        general_layout.addRow("Chu kỳ đồng bộ dữ liệu (giây):", self.sync_time_input)
        
        password_group = QGroupBox("Thay đổi mật khẩu quản trị")
        password_layout = QFormLayout(password_group)
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        password_layout.addRow("Mật khẩu mới:", self.new_password_input)
        password_layout.addRow("Xác nhận mật khẩu:", self.confirm_password_input)

        layout.addWidget(general_group)
        layout.addWidget(password_group)
        return widget

    def _load_settings(self):
        """Tải các cài đặt hiện tại vào các widget."""
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
        self.com_baudrate_input.setCurrentText(str(self._config.get('scale.baud_rate', 9600)))
        self.com_bytesize_input.setCurrentText(str(self._config.get('scale.bytesize', 8)))
        self.com_parity_input.setCurrentText(self._config.get('scale.parity', 'N'))
        self.com_stopbits_input.setCurrentText(str(self._config.get('scale.stop_bits', 1)))
        self.com_timeout_input.setValue(self._config.get('scale.timeout', 1))

        # Camera
        cam_type = self._config.get('camera.qr.type', 'webcam')
        use_webcam = (cam_type == 'webcam')
        self.use_webcam_checkbox.setChecked(use_webcam)
        self.webcam_index_input.setValue(self._config.get('camera.qr.webcam.index', 0))
        self.rtsp_url_input.setText(self._config.get('camera.qr.rtsp.url', ''))
        self._toggle_camera_inputs(use_webcam)

        # General
        self.station_name_input.setText(self._config.get('location_label.name', 'TRẠM CÂN'))
        self.mode_input.setCurrentText(self._config.get('scale_mode.type', 'auto'))
        self.reset_time_input.setValue(self._config.get('reset_time', 15))
        self.sync_time_input.setValue(self._config.get('server.sync_interval', 60))

    def on_save(self):
        """Xử lý sự kiện khi nhấn nút Lưu."""
        # SỬA LỖI: Xóa bỏ phần xác thực mật khẩu ở đây
        # current_hashed_pass = self._config.get('admin.password_hash', hash_password('admin'))
        # verify_dialog = VerifiedDialog(current_hashed_pass, self)
        # if verify_dialog.exec_() != QDialog.Accepted:
        #     return

        new_config = copy.deepcopy(self._config.config)

        # --- Cập nhật Server ---
        new_config['server']['host'] = self.host_input.text()
        new_config['server']['port'] = self.port_input.value()
        new_config['server']['api_token'] = self.token_input.text()
        new_config['server']['sync_interval'] = self.sync_time_input.value()

        # --- Cập nhật NocoDB ---
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

        # --- Cập nhật Scale (COM) ---
        new_config['scale']['com_port'] = self.com_port_input.text()
        new_config['scale']['baud_rate'] = int(self.com_baudrate_input.currentText())
        new_config['scale']['bytesize'] = int(self.com_bytesize_input.currentText())
        new_config['scale']['parity'] = self.com_parity_input.currentText()
        new_config['scale']['stop_bits'] = float(self.com_stopbits_input.currentText())
        new_config['scale']['timeout'] = self.com_timeout_input.value()

        # --- Cập nhật Camera ---
        new_config['camera']['qr']['type'] = 'webcam' if self.use_webcam_checkbox.isChecked() else 'rtsp'
        new_config['camera']['qr']['webcam']['index'] = self.webcam_index_input.value()
        new_config['camera']['qr']['rtsp']['url'] = self.rtsp_url_input.text()

        # --- Cập nhật General ---
        new_config['location_label']['name'] = self.station_name_input.text()
        new_config['scale_mode']['type'] = self.mode_input.currentText()
        new_config['reset_time'] = self.reset_time_input.value()
        
        # --- Cập nhật Mật khẩu ---
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()
        if new_pass:
            if new_pass != confirm_pass:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu mới và mật khẩu xác nhận không khớp!")
                return
            new_config['admin']['password_hash'] = hash_password(new_pass)

        # --- Lưu cấu hình ---
        self._config.set_all(new_config)
        if self._config.save_config():
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt. Một số thay đổi cần khởi động lại ứng dụng để có hiệu lực.")
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể lưu file cấu hình!")
