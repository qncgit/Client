from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAction, QDesktopWidget
from PyQt5.QtCore import QTimer

# Import các thành phần đã được tái cấu trúc
from src.config.config_manager import ConfigManager
from src.data.repository import Repository
from src.data.sync_thread import SyncThread
from src.hardware.camera_thread import CameraThread
from src.hardware.weight_thread import WeightThread
from src.app.main_controller import MainController

from .widgets.header_widget import HeaderWidget
from .widgets.bottom_widget import BottomWidget
from .widgets.step_widgets import (Step1_QRScanWidget, Step2_DriverInfoWidget,
                                 Step3_VehicleInfoWidget, Step4_WeightInfoWidget)
from .dialogs.setting_dialog import SettingDialog
# SỬA LỖI: Import thêm VerifiedDialog và hàm hash_password
from .dialogs.verified_dialog import VerifiedDialog
from src.utils.helpers import hash_password


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- 1. Khởi tạo các thành phần cốt lõi ---
        self.config_manager = ConfigManager()
        self.repository = Repository(self.config_manager)
        self.controller = MainController(self.repository, self.config_manager)

        # --- 2. Thiết lập giao diện ---
        self.setWindowTitle("CÂN TỰ ĐỘNG QNC")
        self.setGeometry(100, 100, 1366, 768)
        self.center_window()

        self.init_ui()
        self.create_actions()
        self.create_menus()

        # --- 3. Khởi tạo và kết nối các luồng ---
        self.init_threads()

        # --- 4. Kết nối tín hiệu và slot ---
        self.connect_signals()

        # --- 5. Khởi động các timer ---
        self.init_timers()

        # Khởi động các luồng
        self.sync_thread.start()
        self.camera_thread.start()
        self.weight_thread.start()

        # Reset lần đầu để đảm bảo giao diện sạch
        self.controller.reset_process()

    def center_window(self):
        """Canh giữa cửa sổ trên màn hình."""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        """Khởi tạo và sắp xếp các widget giao diện."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        self.header = HeaderWidget(self.config_manager)

        # Body (chia 2 cột)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)

        # Cột trái cho Bước 1
        self.step1 = Step1_QRScanWidget()

        # Cột phải cho các bước còn lại
        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(10)
        self.step2 = Step2_DriverInfoWidget()
        self.step3 = Step3_VehicleInfoWidget()
        self.step4 = Step4_WeightInfoWidget()
        right_column_layout.addWidget(self.step2)
        right_column_layout.addWidget(self.step3)
        right_column_layout.addWidget(self.step4)
        right_column_layout.addStretch()


        body_layout.addWidget(self.step1, 5) # Cột trái chiếm 5 phần
        body_layout.addLayout(right_column_layout, 6) # Cột phải chiếm 6 phần

        # Footer
        self.bottom = BottomWidget()

        main_layout.addWidget(self.header)
        main_layout.addLayout(body_layout, 1)
        main_layout.addWidget(self.bottom)

        self.setStyleSheet("background-color: #f0f0f0;")


    def init_threads(self):
        """Khởi tạo các luồng chạy nền."""
        self.sync_thread = SyncThread(self.repository, self.config_manager)
        self.camera_thread = CameraThread(self.config_manager)
        self.weight_thread = WeightThread(self.config_manager)

    def init_timers(self):
        """Khởi tạo các timer cho việc cập nhật UI."""
        self.time_updater = QTimer(self)
        self.time_updater.timeout.connect(self.header.update_time)
        self.time_updater.start(1000)

        # Timer cho thanh progress bar reset
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_reset_progress)
        self.controller.inactivity_timer.timeout.connect(lambda: self.progress_timer.start(100))

    def create_actions(self):
        self.setting_action = QAction("Cài đặt", self)
        self.exit_action = QAction("Thoát", self)

    def create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Tệp")
        file_menu.addAction(self.setting_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

    def connect_signals(self):
        """Kết nối tất cả tín hiệu và slot."""
        # --- Luồng -> UI/Controller ---
        self.weight_thread.weight_update.connect(self.header.update_weight)
        self.weight_thread.weight_update.connect(self.controller.set_current_weight)
        self.weight_thread.connection_status.connect(lambda connected, msg: self.bottom.set_weight_status(connected))

        self.camera_thread.frame_update.connect(self.step1.update_camera_frame)
        self.camera_thread.qr_decoded.connect(self.controller.handle_qr_scan)

        self.sync_thread.sync_status_update.connect(self.handle_sync_status)

        # --- Controller -> UI ---
        self.controller.update_status_signal.connect(self.bottom.set_status)
        self.controller.update_step1_signal.connect(self.step1.update_info)
        self.controller.update_step2_signal.connect(self.step2.update_info)
        self.controller.update_step3_signal.connect(self.step3.update_info)
        self.controller.update_step4_signal.connect(self.step4.update_info)
        self.controller.reset_all_steps_signal.connect(self.reset_all_widgets)
        self.controller.update_mode_signal.connect(self.header.update_mode)

        # --- UI Actions -> Methods ---
        self.setting_action.triggered.connect(self.open_settings)
        self.exit_action.triggered.connect(self.close)

        self.controller.inactivity_timer.timeout.connect(self.controller.reset_process)

    def reset_all_widgets(self):
        """Reset giao diện của tất cả các bước."""
        self.step1.reset()
        self.step2.reset()
        self.step3.reset()
        self.step4.reset()
        self.bottom.update_progress(0, 0)
        self.progress_timer.stop()

    def handle_sync_status(self, message, is_success):
        """Xử lý tín hiệu từ luồng đồng bộ."""
        self.bottom.set_server_status(is_success)
        print(f"Sync status: {message}")

    def open_settings(self):
        """
        Mở cửa sổ cài đặt sau khi xác thực mật khẩu.
        """
        # SỬA LỖI: Thêm logic xác thực mật khẩu tại đây
        current_hashed_pass = self.config_manager.get('admin.password_hash', hash_password('admin'))
        verify_dialog = VerifiedDialog(current_hashed_pass, self)
        
        # Chỉ mở cửa sổ Cài đặt nếu mật khẩu chính xác
        if verify_dialog.exec_() == VerifiedDialog.Accepted:
            dialog = SettingDialog(self.config_manager, self)
            if dialog.exec_() == SettingDialog.Accepted:
                # Tải lại cấu hình và khởi động lại các luồng nếu có thay đổi
                self.config_manager.reload()
                self.repository.load_all_local_data()
                self.header.reload_config()

                # Khởi động lại các luồng để áp dụng config mới
                self.camera_thread.stop()
                self.camera_thread = CameraThread(self.config_manager)
                self.camera_thread.frame_update.connect(self.step1.update_camera_frame)
                self.camera_thread.qr_decoded.connect(self.controller.handle_qr_scan)
                self.camera_thread.start()

                self.weight_thread.stop()
                self.weight_thread = WeightThread(self.config_manager)
                self.weight_thread.weight_update.connect(self.header.update_weight)
                self.weight_thread.weight_update.connect(self.controller.set_current_weight)
                self.weight_thread.connection_status.connect(lambda c,m: self.bottom.set_weight_status(c))
                self.weight_thread.start()

    def update_reset_progress(self):
        """Cập nhật thanh tiến trình đếm ngược để reset."""
        elapsed_ms = self.controller.inactivity_timer.remainingTime()
        total_ms = self.controller.inactivity_timer.interval()
        if elapsed_ms >= 0 and total_ms > 0:
            progress = 100 - int((elapsed_ms / total_ms) * 100)
            self.bottom.update_progress(progress, total_ms / 1000 - elapsed_ms / 1000)
        else:
            self.bottom.update_progress(0, 0)

    def closeEvent(self, event):
        """Dừng các luồng trước khi đóng ứng dụng."""
        print("Đang đóng ứng dụng...")
        self.camera_thread.stop()
        self.weight_thread.stop()
        self.sync_thread.stop()
        event.accept()