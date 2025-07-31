# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/main_window.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDesktopWidget, QSizePolicy
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from qfluentwidgets import (FluentWindow, FluentIcon as FIF, InfoBar, 
                            InfoBarPosition, CardWidget)

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

        self.sync_thread.start()
        self.camera_thread.start()
        self.weight_thread.start()
        self.controller.reset_process()

        self.is_qr_lock_pending = False

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
        self.step1 = Step1_QRScanWidget()
        self.step2 = Step2_DriverInfoWidget()
        self.step3 = Step3_VehicleInfoWidget()
        self.step4 = Step4_WeightInfoWidget()

        # Bọc các widget bằng CardWidget và thiết lập size policy
        left_card = CardWidget()
        left_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(self.step1, stretch=1)

        right_card = CardWidget()
        right_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        # Giảm chiều cao step2 và step3, tăng step4
        right_layout.addWidget(self.step2, stretch=1)
        right_layout.addWidget(self.step3, stretch=1)
        right_layout.addWidget(self.step4, stretch=3)

        # Sử dụng QHBoxLayout để chia tỷ lệ 2:3
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        content_layout.addWidget(left_card)
        content_layout.addWidget(right_card)
        content_layout.setStretchFactor(left_card, 2)
        content_layout.setStretchFactor(right_card, 3)

        main_layout.addWidget(self.header)
        main_layout.addLayout(content_layout, 1)
        main_layout.addWidget(self.bottom)

        # Đặt stretch factor cho layout chính
        main_layout.setStretchFactor(content_layout, 1)

    def init_threads(self):
        self.sync_thread = SyncThread(self.repository, self.config_manager)
        self.camera_thread = CameraThread(self.config_manager)
        self.weight_thread = WeightThread(self.config_manager)

    def init_timers(self):
        self.time_updater = QTimer(self)
        self.time_updater.timeout.connect(self.header.update_time)
        self.time_updater.start(1000)

        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(50)  # Cập nhật mỗi 50ms
        self.progress_timer.timeout.connect(self.update_reset_progress)
        # Kết nối với timer của controller
        self.controller.inactivity_timer.timeout.connect(self.on_inactivity_timeout)

        self.qr_confirm_timer = QTimer(self)
        self.qr_confirm_timer.setInterval(5000)  # 5 giây
        self.qr_confirm_timer.setSingleShot(True)
        self.qr_confirm_timer.timeout.connect(self.on_qr_confirmed)

    def on_inactivity_timeout(self):
        """Xử lý khi hết thời gian chờ"""
        self.progress_timer.stop()
        self.bottom.update_progress(0, 0)
        self.controller.reset_process()

    def start_progress_timer(self, _):
        """Bắt đầu đếm ngược khi quét mã thành công"""
        self.progress_timer.start()

    def on_qr_decoded(self, qr_data):
        """Xử lý khi quét mã QR thành công"""
        print("QR scanned - Waiting for confirmation")
        
        # Luôn lock QR frame khi quét mã thành công
        self.step1.lock_qr_frame()
        
        # Khởi động timer đếm ngược và progress bar ngay khi quét QR
        self.restart_progress_timer()
        
        # Nếu lần đầu (khởi tạo cân), sau 5s sẽ unlock để cho phép quét xác nhận
        if self.controller.current_state == self.controller.STATE_IDLE:
            self.is_qr_lock_pending = True  # Đánh dấu cần unlock sau 5s
            # Đảm bảo timer không bị trùng lặp
            if self.qr_confirm_timer.isActive():
                self.qr_confirm_timer.stop()
            self.qr_confirm_timer.start()
            self.bottom.set_status("Đang xác nhận mã QR...", "blue")
        
        # Nếu lần xác thực lưu, giữ lock QR (không unlock sau 5s)
        elif self.controller.current_state == self.controller.STATE_WAITING_CONFIRM:
            self.is_qr_lock_pending = False  # Không unlock sau 5s
            self.bottom.set_status("Đang xác nhận mã QR để lưu...", "blue")
            # QR xác nhận sẽ được xử lý bởi controller.handle_qr_scan

    def restart_progress_timer(self):
        """Khởi động lại timer đếm ngược và progress bar"""
        if not self.progress_timer.isActive():
            self.progress_timer.start()
        self.bottom.update_progress(100, self.controller.inactivity_timer.interval() / 1000)
            
    def on_qr_confirmed(self):
        """Xử lý sau khi đã xác nhận QR (sau 5s)"""
        print("QR confirmed - Starting process")
        
        # Chỉ unlock QR nếu đang chờ unlock (quét lần đầu) và trạng thái đã chuyển sang PROCESSING
        if self.is_qr_lock_pending and self.controller.current_state == self.controller.STATE_PROCESSING:
            self.step1.unlock_qr_frame()
            self.is_qr_lock_pending = False
            self.bottom.set_status("Mã QR đã được xác nhận. Đưa xe lên cân và chờ cân xong.", "green")
        
        # Cập nhật lại progress bar (không cần khởi động lại vì đã khởi động trong on_qr_decoded)
        self.bottom.update_progress(100, self.controller.inactivity_timer.interval() / 1000)

    def on_weighing_complete(self):
        """Xử lý khi đã cân xong, cho phép quét QR để xác nhận lưu"""
        self.step1.unlock_qr_frame()
        self.is_qr_lock_pending = False
        self.bottom.set_status("Quét lại mã QR để xác nhận lưu kết quả cân", "blue")

    def update_reset_progress(self):
        elapsed_ms = self.controller.inactivity_timer.remainingTime()
        total_ms = self.controller.inactivity_timer.interval()
        
        if elapsed_ms > 0 and total_ms > 0:
            # Đảo ngược logic - progress giảm dần từ 100 về 0
            progress = int((elapsed_ms / total_ms) * 100)
            remaining_seconds = elapsed_ms / 1000
            self.bottom.update_progress(progress, remaining_seconds)
        else:
            self.progress_timer.stop()
            self.bottom.update_progress(0, 0)

    def connect_signals(self):
        # ✨ SỬA ĐỔI: Kết nối tín hiệu từ nút cài đặt mới
        self.bottom.settings_button_clicked.connect(self.open_settings)
    
        self.weight_thread.weight_update.connect(self.header.update_weight)
        self.weight_thread.weight_update.connect(self.controller.set_current_weight)
        self.weight_thread.connection_status.connect(self.bottom.set_weight_status)

        self.camera_thread.frame_update.connect(self.step1.update_camera_frame)
        self.camera_thread.qr_decoded.connect(self.controller.handle_qr_scan)
        # Thêm kết nối cho sự kiện quét mã thành công
        self.camera_thread.qr_decoded.connect(self.on_qr_decoded)
        
        # Kết nối tín hiệu từ controller khi cân xong để bật lại chế độ QR
        self.controller.weighing_complete_signal.connect(self.on_weighing_complete)

        self.sync_thread.sync_status_update.connect(self.handle_sync_status)

        self.controller.update_status_signal.connect(self.bottom.set_status)
        self.controller.update_step1_signal.connect(self.step1.update_info)
        self.controller.update_step2_signal.connect(self.step2.update_info)
        self.controller.update_step3_signal.connect(self.step3.update_info)
        self.controller.update_step4_signal.connect(self.step4.update_info)
        self.controller.reset_all_steps_signal.connect(self.reset_all_widgets)
        self.controller.update_mode_signal.connect(self.header.update_mode)

        self.controller.inactivity_timer.timeout.connect(self.controller.reset_process)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_dynamic_font_size()

    def _update_dynamic_font_size(self):
        base_height = 768
        base_font_size = 12
        max_font_size = 24
        h = self.height()
        if h <= base_height:
            font_size = base_font_size
        else:
            font_size = min(base_font_size + int((h - base_height) / 100), max_font_size)
        # Áp dụng cho các dialog SettingDialog nếu đang mở
        for dialog in self.findChildren(SettingDialog):
            dialog.update_font_size(font_size)
        # Áp dụng cho các step widget nếu có phương thức update_font_size
        for step_widget in [self.step1, self.step2, self.step3, self.step4]:
            if hasattr(step_widget, "update_font_size"):
                step_widget.update_font_size(font_size)

    def reset_all_widgets(self):
        """Reset các widget về trạng thái ban đầu"""
        # Đảm bảo luôn unlock QR frame khi reset form
        self.step1.unlock_qr_frame()
        self.is_qr_lock_pending = False  # Reset cờ khi reset form
        
        # Reset dữ liệu của các widget
        self.step1.reset_data()  
        self.step2.reset()
        self.step3.reset()
        self.step4.reset()
        
        # Reset progress bar
        self.bottom.update_progress(0, 0)
        
        # Dừng các timer nếu đang chạy
        if self.progress_timer.isActive():
            self.progress_timer.stop()
        if self.qr_confirm_timer.isActive():
            self.qr_confirm_timer.stop()

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

    def closeEvent(self, event):
        print("Đang đóng ứng dụng...")
        self.camera_thread.stop()
        self.weight_thread.stop()
        self.sync_thread.stop()
        event.accept()