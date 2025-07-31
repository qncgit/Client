# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/dialogs/setting_dialog.py
import copy
from PyQt5.QtWidgets import QDialog, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QStackedWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from qfluentwidgets import (FluentIcon as FIF, SegmentedWidget, PrimaryPushButton, PushButton, MessageBox,
                            LineEdit, SpinBox, ComboBox, SwitchButton, CardWidget, 
                            TitleLabel, BodyLabel)
from src.utils.helpers import Common

class SettingDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager

        self.setWindowTitle("Cài đặt hệ thống")
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        self.setMinimumSize(800, 600)

        # --- Layouts ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 15)
        self.main_layout.setSpacing(0)

        # --- Top Navigation Bar ---
        self.navigation = SegmentedWidget(self)
        self.main_layout.addWidget(self.navigation)

        # --- Content Pages ---
        self.stackedWidget = QStackedWidget(self)
        self.main_layout.addWidget(self.stackedWidget, 1)
        
        self.pages = {}

        self._create_and_setup_pages()
        
        # --- Nút Lưu và Hủy ---
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(20, 10, 20, 0)
        self.button_layout.addStretch(1)
        self.saveButton = PrimaryPushButton(FIF.SAVE, "Lưu cài đặt")
        self.cancelButton = PushButton(FIF.CANCEL, "Hủy")
        self.button_layout.addWidget(self.saveButton)
        self.button_layout.addWidget(self.cancelButton)
        self.main_layout.addLayout(self.button_layout)

        # --- Kết nối tín hiệu ---
        self.navigation.currentItemChanged.connect(self.on_nav_item_changed)
        
        self.saveButton.clicked.connect(self.on_save)
        self.cancelButton.clicked.connect(self.reject)

        self._load_settings()

    def _create_and_setup_pages(self):
        page_configs = {
            "serverPage": ("Máy chủ & API", FIF.SETTING, self._setup_server_ui),
            "comPage": ("Cổng COM (Cân)", FIF.SETTING, self._setup_com_ui),
            "cameraPage": ("Camera QR", FIF.SETTING, self._setup_camera_ui),
            "generalPage": ("Cài đặt chung", FIF.SETTING, self._setup_general_ui)
        }

        for index, (key, (text, icon, setup_func)) in enumerate(page_configs.items()):
            page = QWidget()
            self.pages[key] = page
            self.stackedWidget.addWidget(page)
            self.navigation.insertItem(index, key, text, icon=icon)
            setup_func(page)

    def on_nav_item_changed(self, routeKey: str):
        widget_to_show = self.pages.get(routeKey)
        if widget_to_show:
            self.stackedWidget.setCurrentWidget(widget_to_show)

    # ... (các hàm _setup... và _load_settings... giữ nguyên) ...
    def _create_form_card(self, parent_widget, title):
        card = CardWidget(parent_widget)
        container_layout = QVBoxLayout(card)
        container_layout.setContentsMargins(20, 15, 20, 20)
        container_layout.setSpacing(10)
        title_label = TitleLabel(title)
        title_label.setProperty('level', 'h3')
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        container_layout.addWidget(title_label)
        container_layout.addLayout(grid_layout)
        return card, grid_layout

    def _add_grid_row(self, grid_layout, label_text, widget):
        row = grid_layout.rowCount()
        label = BodyLabel(label_text)
        grid_layout.addWidget(label, row, 0)
        grid_layout.addWidget(widget, row, 1)

    def _setup_server_ui(self, page: QWidget):
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 10, 20, 20)
        page_layout.setSpacing(10)

        server_card, server_grid = self._create_form_card(page, "Kết nối máy chủ")
        self.host_input = LineEdit()
        self.port_input = SpinBox()
        self.port_input.setRange(1, 65535)
        self.token_input = LineEdit()
        self._add_grid_row(server_grid, "Host/IP Máy chủ:", self.host_input)
        self._add_grid_row(server_grid, "Port:", self.port_input)
        self._add_grid_row(server_grid, "API Token (xc-token):", self.token_input)
        server_grid.setColumnStretch(1, 1)

        noco_card, noco_grid = self._create_form_card(page, "NocoDB API IDs")
        self.project_id_input = LineEdit()
        self.table_id_phieu_can_input = LineEdit()
        self.table_id_lenh_can_input = LineEdit()
        self.view_id_lenh_can_input = LineEdit()
        self.table_id_phuong_tien_input = LineEdit()
        self.view_id_phuong_tien_input = LineEdit()
        self.table_id_nhan_vien_input = LineEdit()
        self.view_id_nhan_vien_input = LineEdit()
        self._add_grid_row(noco_grid, "Base ID:", self.project_id_input)
        self._add_grid_row(noco_grid, "Table ID (Lịch sử cân):", self.table_id_phieu_can_input)
        self._add_grid_row(noco_grid, "Table ID (Lệnh cân):", self.table_id_lenh_can_input)
        self._add_grid_row(noco_grid, "View ID (Lệnh cân):", self.view_id_lenh_can_input)
        self._add_grid_row(noco_grid, "Table ID (Phương tiện):", self.table_id_phuong_tien_input)
        self._add_grid_row(noco_grid, "View ID (Phương tiện):", self.view_id_phuong_tien_input)
        self._add_grid_row(noco_grid, "Table ID (Nhân viên):", self.table_id_nhan_vien_input)
        self._add_grid_row(noco_grid, "View ID (Nhân viên):", self.view_id_nhan_vien_input)
        noco_grid.setColumnStretch(1, 1)

        page_layout.addWidget(server_card)
        page_layout.addWidget(noco_card)
        page_layout.addStretch()

    def _setup_com_ui(self, page: QWidget):
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 10, 20, 20)
        com_card, com_grid = self._create_form_card(page, "Cấu hình cổng Serial (Đầu cân)")
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
        self._add_grid_row(com_grid, "Cổng COM (vd: COM1):", self.com_port_input)
        self._add_grid_row(com_grid, "Baudrate:", self.com_baudrate_input)
        self._add_grid_row(com_grid, "Bytesize:", self.com_bytesize_input)
        self._add_grid_row(com_grid, "Parity (N-None, E-Even, O-Odd):", self.com_parity_input)
        self._add_grid_row(com_grid, "Stop bits:", self.com_stopbits_input)
        self._add_grid_row(com_grid, "Timeout (giây):", self.com_timeout_input)
        com_grid.setColumnStretch(1, 1)
        page_layout.addWidget(com_card)
        page_layout.addStretch()

    def _setup_camera_ui(self, page: QWidget):
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 10, 20, 20)
        cam_card, cam_grid = self._create_form_card(page, "Cấu hình Camera quét mã QR")
        self.cam_enabled_switch = SwitchButton("Bật Camera QR")
        self.cam_type_input = ComboBox()
        self.cam_type_input.addItems(['webcam', 'rtsp'])
        self.webcam_index_input = SpinBox()
        self.rtsp_url_input = LineEdit()
        self.cam_type_input.currentTextChanged.connect(self._toggle_camera_inputs)
        cam_grid.addWidget(self.cam_enabled_switch, 0, 0, 1, 2)
        self._add_grid_row(cam_grid, "Loại Camera:", self.cam_type_input)
        self._add_grid_row(cam_grid, "Chỉ số Webcam:", self.webcam_index_input)
        self._add_grid_row(cam_grid, "URL RTSP:", self.rtsp_url_input)
        cam_grid.setColumnStretch(1, 1)
        page_layout.addWidget(cam_card)
        page_layout.addStretch()
        
    def _toggle_camera_inputs(self, cam_type):
        self.webcam_index_input.setEnabled(cam_type == 'webcam')
        self.rtsp_url_input.setEnabled(cam_type != 'webcam')

    def _setup_general_ui(self, page: QWidget):
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 10, 20, 20)
        page_layout.setSpacing(10)
        general_card, general_grid = self._create_form_card(page, "Cài đặt chung")
        self.station_name_input = LineEdit()
        self.mode_input = ComboBox()
        self.mode_input.addItems(['auto', 'in', 'out'])
        self.mode_desc_input = LineEdit()
        self.reset_time_input = SpinBox()
        self.reset_time_input.setRange(5, 300)
        self.sync_time_input = SpinBox()
        self.sync_time_input.setRange(10, 600)
        self._add_grid_row(general_grid, "Tên trạm cân:", self.station_name_input)
        self._add_grid_row(general_grid, "Chế độ cân (auto/in/out):", self.mode_input)
        self._add_grid_row(general_grid, "Mô tả chế độ cân:", self.mode_desc_input)
        self._add_grid_row(general_grid, "Thời gian tự reset (giây):", self.reset_time_input)
        self._add_grid_row(general_grid, "Chu kỳ đồng bộ (giây):", self.sync_time_input)
        general_grid.setColumnStretch(1, 1)

        password_card, password_grid = self._create_form_card(page, "Thay đổi mật khẩu quản trị")
        self.new_password_input = LineEdit()
        self.new_password_input.setEchoMode(LineEdit.Password)
        self.confirm_password_input = LineEdit()
        self.confirm_password_input.setEchoMode(LineEdit.Password)
        self._add_grid_row(password_grid, "Mật khẩu mới:", self.new_password_input)
        self._add_grid_row(password_grid, "Xác nhận mật khẩu:", self.confirm_password_input)
        password_grid.setColumnStretch(1, 1)

        page_layout.addWidget(general_card)
        page_layout.addWidget(password_card)
        page_layout.addStretch()

    def _load_settings(self):
        self.host_input.setText(self._config.get('server.host', ''))
        self.port_input.setValue(self._config.get('server.port', 8080))
        self.token_input.setText(self._config.get('server.api_token', ''))
        self.sync_time_input.setValue(self._config.get('server.sync_interval', 60))
        
        self.project_id_input.setText(self._config.get('nocodb.base.id', ''))
        def load_table_ids(name, table_widget, view_widget, view_name):
            table = self._config.get_nocodb_table_by_name(name)
            if table:
                table_widget.setText(table.get('id',''))
                view = self._config.get_nocodb_view_by_name(table, view_name)
                if view: view_widget.setText(view.get('id',''))
        
        load_table_ids("Thông tin nhân viên", self.table_id_nhan_vien_input, self.view_id_nhan_vien_input, "Thongtinnhanvien")
        load_table_ids("Thông tin phương tiện", self.table_id_phuong_tien_input, self.view_id_phuong_tien_input, "Thongtinphuongtien")
        load_table_ids("Thông tin lệnh cân", self.table_id_lenh_can_input, self.view_id_lenh_can_input, "Thongtinlenhcan")
        
        pc_table = self._config.get_nocodb_table_by_name("Lịch sử cân")
        if pc_table: self.table_id_phieu_can_input.setText(pc_table.get('id', ''))
        
        self.com_port_input.setText(self._config.get('scale.com_port', 'COM1'))
        self.com_baudrate_input.setText(str(self._config.get('scale.baud_rate', 9600)))
        self.com_bytesize_input.setText(str(self._config.get('scale.bytesize', 8)))
        self.com_parity_input.setText(self._config.get('scale.parity', 'N'))
        self.com_stopbits_input.setText(str(self._config.get('scale.stop_bits', 1)))
        self.com_timeout_input.setValue(self._config.get('scale.timeout', 1))

        self.cam_enabled_switch.setChecked(self._config.get('camera.qr.enabled', False))
        cam_type = self._config.get('camera.qr.type', 'webcam')
        self.cam_type_input.setCurrentText(cam_type)
        self.webcam_index_input.setValue(self._config.get('camera.qr.webcam.index', 0))
        self.rtsp_url_input.setText(self._config.get('camera.qr.rtsp.url', ''))
        self._toggle_camera_inputs(cam_type)

        self.station_name_input.setText(self._config.get('location_label.name', 'TRẠM CÂN'))
        self.mode_input.setCurrentText(self._config.get('scale_mode.type', 'auto'))
        self.mode_desc_input.setText(self._config.get('scale_mode.description', ''))
        self.reset_time_input.setValue(self._config.get('reset_time', 15))
        
    def on_save(self):
        new_config = copy.deepcopy(self._config.config)
        # ... (logic sao chép config giữ nguyên) ...
        new_config['server']['host'] = self.host_input.text()
        new_config['server']['port'] = self.port_input.value()
        new_config['server']['api_token'] = self.token_input.text()
        new_config['server']['sync_interval'] = self.sync_time_input.value()
        new_config['nocodb']['base']['id'] = self.project_id_input.text()

        def update_table_ids(name, table_widget, view_widget, view_name):
            table = self._config.get_nocodb_table_by_name(name)
            if table:
                table['id'] = table_widget.text()
                view = self._config.get_nocodb_view_by_name(table, view_name)
                if view: view['id'] = view_widget.text()

        update_table_ids("Thông tin nhân viên", self.table_id_nhan_vien_input, self.view_id_nhan_vien_input, "Thongtinnhanvien")
        update_table_ids("Thông tin phương tiện", self.table_id_phuong_tien_input, self.view_id_phuong_tien_input, "Thongtinphuongtien")
        update_table_ids("Thông tin lệnh cân", self.table_id_lenh_can_input, self.view_id_lenh_can_input, "Thongtinlenhcan")
        
        pc_table = self._config.get_nocodb_table_by_name("Lịch sử cân")
        if pc_table: pc_table['id'] = self.table_id_phieu_can_input.text()

        new_config['scale']['com_port'] = self.com_port_input.text()
        new_config['scale']['baud_rate'] = int(self.com_baudrate_input.text())
        new_config['scale']['bytesize'] = int(self.com_bytesize_input.text())
        new_config['scale']['parity'] = self.com_parity_input.text()
        new_config['scale']['stop_bits'] = float(self.com_stopbits_input.text())
        new_config['scale']['timeout'] = self.com_timeout_input.value()

        new_config['camera']['qr']['enabled'] = self.cam_enabled_switch.isChecked()
        new_config['camera']['qr']['type'] = self.cam_type_input.text()
        new_config['camera']['qr']['webcam']['index'] = self.webcam_index_input.value()
        new_config['camera']['qr']['rtsp']['url'] = self.rtsp_url_input.text()
        
        new_config['location_label']['name'] = self.station_name_input.text()
        new_config['scale_mode']['type'] = self.mode_input.text()
        new_config['scale_mode']['description'] = self.mode_desc_input.text()
        new_config['reset_time'] = self.reset_time_input.value()
        
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()
        if new_pass:
            if new_pass != confirm_pass:
                m = MessageBox('Lỗi', 'Mật khẩu mới và mật khẩu xác nhận không khớp!', self)
                m.exec()
                return
            new_config['admin']['password_hash'] = Common.hash_password(new_pass)

        # Lưu config
        if self._config.save_config(new_config):
            self.settings_saved.emit()
            
            # ✨ SỬA LỖI: Đóng dialog TRƯỚC khi hiển thị thông báo
            # parent() ở đây chính là MainWindow
            main_window = self.parent() 
            self.accept()
            
            # Hiển thị thông báo thành công trên cửa sổ chính
            MessageBox.success('Thành công', 'Đã lưu cài đặt!', main_window)
        else:
            MessageBox.error('Lỗi', 'Không thể lưu file cấu hình!', self)

    def update_font_size(self, font_size):
        widgets = [
            self.host_input, self.port_input, self.token_input,
            self.project_id_input, self.table_id_phieu_can_input, self.table_id_lenh_can_input,
            self.view_id_lenh_can_input, self.table_id_phuong_tien_input, self.view_id_phuong_tien_input,
            self.table_id_nhan_vien_input, self.view_id_nhan_vien_input,
            self.com_port_input, self.com_baudrate_input, self.com_bytesize_input,
            self.com_parity_input, self.com_stopbits_input, self.com_timeout_input,
            self.cam_enabled_switch, self.cam_type_input, self.webcam_index_input, self.rtsp_url_input,
            self.station_name_input, self.mode_input, self.mode_desc_input,
            self.reset_time_input, self.sync_time_input,
            self.new_password_input, self.confirm_password_input
        ]
        for w in widgets:
            if hasattr(w, "setFont"):
                f = w.font()
                f.setPointSize(font_size)
                w.setFont(f)
        # Cập nhật font cho các label trong CardWidget
        for card in self.findChildren((TitleLabel, BodyLabel)):
            f = card.font()
            f.setPointSize(font_size)
            card.setFont(f)