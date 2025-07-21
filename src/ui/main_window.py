# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/main_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from qfluentwidgets import (FluentWindow, FluentIcon as FIF, InfoBar, 
                            InfoBarPosition, Action)

from src.config.config_manager import ConfigManager
from src.data.repository import Repository
from src.data.sync_thread import SyncThread
from src.hardware.camera_thread import CameraThread
from src.hardware.weight_thread import WeightThread
from src.app.main_controller import MainController
from src.utils.helpers import Common

from .widgets.header_widget import HeaderWidget
from .widgets.bottom_widget import BottomWidget
from .widgets.step_widgets import (Step1_QRScanWidget, Step2_DriverInfoWidget,
                                 Step3_VehicleInfoWidget, Step4_WeightInfoWidget)
from .dialogs.setting_dialog import SettingDialog
from .dialogs.verified_dialog import VerifiedDialog

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.repository = Repository(self.config_manager)
        self.controller = MainController(self.repository, self.config_manager)

        self.setWindowTitle("HỆ THỐNG CÂN TỰ ĐỘNG QNC")
        self.setGeometry(100, 100, 1366, 768)
        self.center_window()
        
        self.setMicaEffectEnabled(True)
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        self.main_interface = QWidget()
        self.main_interface.setObjectName("main_interface")
        self.init_ui()

        self.addSubInterface(self.main_interface, "main_icon", "Trang chính")
        self.navigationInterface.setCurrentItem("main_icon")
        self.navigationInterface.setCollapsible(False)
        self.navigationInterface.setExpandWidth(0)
        self.navigationInterface.hide()

        self.init_threads()
        self.connect_signals()
        self.init_timers()
        # ✨ SỬA ĐỔI: Không cần thêm nút vào title bar nữa
        # self.add_setting_action() 

        self.sync_thread.start()
        self.camera_thread.start()
        self.weight_thread.start()
        self.controller.reset_process()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        main_layout = QVBoxLayout(self.main_interface)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 5, 10, 5)

        self.header = HeaderWidget(self.config_manager)
        self.bottom = BottomWidget()
        body_layout = QHBoxLayout()
        body_layout.setSpacing(10)

        self.step1 = Step1_QRScanWidget()
        right_column_layout = QVBoxLayout()
        right_column_layout.setSpacing(10)
        self.step2 = Step2_DriverInfoWidget()
        self.step3 = Step3_VehicleInfoWidget()
        self.step4 = Step4_WeightInfoWidget()
        right_column_layout.addWidget(self.step2)
        right_column_layout.addWidget(self.step3)
        right_column_layout.addWidget(self.step4)
        right_column_layout.addStretch()

        body_layout.addWidget(self.step1, 5)
        body_layout.addLayout(right_column_layout, 6)
        
        main_layout.addWidget(self.header)
        main_layout.addLayout(body_layout, 1)
        main_layout.addWidget(self.bottom)
        
    # ✨ SỬA ĐỔI: Xóa hoặc vô hiệu hóa hàm này
    # def add_setting_action(self):
    #     self.actionSetting = Action(FIF.SETTING, "Cài đặt", triggered=self.open_settings)
    #     self.setting_action = self.titleBar.addAction(self.actionSetting)

    def init_threads(self):
        self.sync_thread = SyncThread(self.repository, self.config_manager)
        self.camera_thread = CameraThread(self.config_manager)
        self.weight_thread = WeightThread(self.config_manager)

    def init_timers(self):
        self.time_updater = QTimer(self)
        self.time_updater.timeout.connect(self.header.update_time)
        self.time_updater.start(1000)

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_reset_progress)
        self.controller.inactivity_timer.timeout.connect(lambda: self.progress_timer.start(100))
    
    def connect_signals(self):
        # ✨ SỬA ĐỔI: Kết nối tín hiệu từ nút cài đặt mới
        self.bottom.settings_button_clicked.connect(self.open_settings)
    
        self.weight_thread.weight_update.connect(self.header.update_weight)
        self.weight_thread.weight_update.connect(self.controller.set_current_weight)
        self.weight_thread.connection_status.connect(self.bottom.set_weight_status)

        self.camera_thread.frame_update.connect(self.step1.update_camera_frame)
        self.camera_thread.qr_decoded.connect(self.controller.handle_qr_scan)

        self.sync_thread.sync_status_update.connect(self.handle_sync_status)

        self.controller.update_status_signal.connect(self.bottom.set_status)
        self.controller.update_step1_signal.connect(self.step1.update_info)
        self.controller.update_step2_signal.connect(self.step2.update_info)
        self.controller.update_step3_signal.connect(self.step3.update_info)
        self.controller.update_step4_signal.connect(self.step4.update_info)
        self.controller.reset_all_steps_signal.connect(self.reset_all_widgets)
        self.controller.update_mode_signal.connect(self.header.update_mode)

        self.controller.inactivity_timer.timeout.connect(self.controller.reset_process)

    # ... (các hàm còn lại giữ nguyên) ...
    def reset_all_widgets(self):
        self.step1.reset()
        self.step2.reset()
        self.step3.reset()
        self.step4.reset()
        self.bottom.update_progress(0, 0)
        if self.progress_timer:
            self.progress_timer.stop()

    def handle_sync_status(self, message, is_success):
        self.bottom.set_server_status(is_success, message)

    def open_settings(self):
        current_hashed_pass = self.config_manager.get('admin.password_hash', Common.hash_password('admin'))
        verify_dialog = VerifiedDialog(current_hashed_pass, self)
        
        if verify_dialog.exec():
            dialog = SettingDialog(self.config_manager, self)
            dialog.settings_saved.connect(self.on_settings_saved)
            dialog.exec()

    def on_settings_saved(self):
        self.config_manager.reload()
        self.repository.load_all_local_data()
        self.header.reload_config()
        self.controller.reset_process() 
        
        InfoBar.success(
            'Thành công', 'Cài đặt đã được áp dụng!',
            duration=3000, position=InfoBarPosition.TOP_RIGHT, parent=self
        )

        self.camera_thread.stop()
        self.camera_thread = CameraThread(self.config_manager)
        self.camera_thread.frame_update.connect(self.step1.update_camera_frame)
        self.camera_thread.qr_decoded.connect(self.controller.handle_qr_scan)
        self.camera_thread.start()

        self.weight_thread.stop()
        self.weight_thread = WeightThread(self.config_manager)
        self.weight_thread.weight_update.connect(self.header.update_weight)
        self.weight_thread.weight_update.connect(self.controller.set_current_weight)
        self.weight_thread.connection_status.connect(self.bottom.set_weight_status)
        self.weight_thread.start()

    def update_reset_progress(self):
        elapsed_ms = self.controller.inactivity_timer.remainingTime()
        total_ms = self.controller.inactivity_timer.interval()
        if elapsed_ms >= 0 and total_ms > 0:
            progress = 100 - int((elapsed_ms / total_ms) * 100)
            self.bottom.update_progress(progress, total_ms / 1000 - elapsed_ms / 1000)
        else:
            self.bottom.update_progress(0, 0)

    def closeEvent(self, event):
        print("Đang đóng ứng dụng...")
        self.camera_thread.stop()
        self.weight_thread.stop()
        self.sync_thread.stop()
        event.accept()