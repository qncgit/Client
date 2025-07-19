from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime

class MainController(QObject):
    """
    Bộ điều khiển trung tâm, xử lý toàn bộ logic nghiệp vụ của ứng dụng.
    """
    update_status_signal = pyqtSignal(str, str)
    update_step1_signal = pyqtSignal(dict)
    update_step2_signal = pyqtSignal(dict)
    update_step3_signal = pyqtSignal(dict)
    update_step4_signal = pyqtSignal(dict)
    reset_all_steps_signal = pyqtSignal()
    update_mode_signal = pyqtSignal(str)
    
    STATE_IDLE = "IDLE"
    STATE_PROCESSING = "PROCESSING"
    STATE_WAITING_CONFIRM = "WAITING_CONFIRM"

    def __init__(self, repository, config_manager):
        super().__init__()
        self._repo = repository
        self._config = config_manager
        
        self.current_state = self.STATE_IDLE
        self.current_weight = 0
        self.phieu_can_hien_tai = {}

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.reset_process)

    def set_current_weight(self, weight):
        self.current_weight = weight

    def handle_qr_scan(self, qr_data):
        self.restart_inactivity_timer()
        
        parts = qr_data.strip().split('_')
        if len(parts) != 3:
            self.update_status_signal.emit(f"Lỗi mã QR: Sai cấu trúc. ({qr_data})", "red")
            return
            
        ma_lenh, ma_lai_xe, bien_so_xe = parts
        
        if self.current_state == self.STATE_IDLE:
            self._handle_new_weighing_request(ma_lenh, ma_lai_xe, bien_so_xe)
        elif self.current_state == self.STATE_WAITING_CONFIRM:
            self._handle_save_confirmation(ma_lenh)
        else:
            self.update_status_signal.emit("Hệ thống đang xử lý, vui lòng chờ.", "orange")

    def _handle_new_weighing_request(self, ma_lenh, ma_lai_xe, bien_so_xe):
        self.current_state = self.STATE_PROCESSING
        self.update_status_signal.emit(f"Đã nhận lệnh '{ma_lenh}'. Đưa xe vào vị trí cân ổn định.", "blue")
        
        lenh_can_details = self._repo.get_lenh_can_by_id(ma_lenh)
        lai_xe_details = self._repo.get_nhan_vien_by_id(ma_lai_xe)
        phuong_tien_details = self._repo.get_phuong_tien_by_bks(bien_so_xe)
        
        lenh_can_info = lenh_can_details if lenh_can_details else {'Mã lệnh': ma_lenh}
        lai_xe_info = lai_xe_details if lai_xe_details else {'Mã lái xe': ma_lai_xe, 'Họ và tên': ma_lai_xe}
        phuong_tien_info = phuong_tien_details if phuong_tien_details else {'Biển số': bien_so_xe}

        phieu_can_cho = self._repo.find_phieu_can_dang_cho(ma_lenh)
        
        self.phieu_can_hien_tai = self._build_weighing_ticket(
            lenh_can_info, lai_xe_info, phuong_tien_info, phieu_can_cho
        )

        self.update_step1_signal.emit(lenh_can_info)
        self.update_step2_signal.emit(lai_xe_info)
        self.update_step3_signal.emit(phuong_tien_info)
        self.update_step4_signal.emit(self.phieu_can_hien_tai)
        
        stable_time = self._config.get('app.stable_time', 3) # Thêm key này vào config nếu muốn thay đổi
        QTimer.singleShot(stable_time * 1000, self._execute_weighing)

    def _execute_weighing(self):
        mode = self._config.get('scale_mode.type', 'auto')
        
        if self.phieu_can_hien_tai.get('Cân lần 1 (Kg)') is None and mode in ['auto', 'in']:
            self.phieu_can_hien_tai['Cân lần 1 (Kg)'] = self.current_weight
            self.phieu_can_hien_tai['Thời gian cân lần 1'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            self.update_status_signal.emit("Đã ghi nhận cân lần 1. Quét lại mã QR để xác nhận lưu.", "green")
        elif self.phieu_can_hien_tai.get('Cân lần 1 (Kg)') is not None and mode in ['auto', 'out']:
            self.phieu_can_hien_tai['Cân lần 2 (Kg)'] = self.current_weight
            self.phieu_can_hien_tai['Thời gian cân lần 2'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            self._calculate_final_weight()
            self.update_status_signal.emit("Đã ghi nhận cân lần 2. Quét lại mã QR để xác nhận lưu.", "green")
        else:
            self.update_status_signal.emit(f"Chế độ '{mode}' không cho phép thực hiện thao tác này.", "red")
            self.reset_process()
            return

        self.current_state = self.STATE_WAITING_CONFIRM
        self.update_step4_signal.emit(self.phieu_can_hien_tai)
        self.restart_inactivity_timer()

    def _handle_save_confirmation(self, ma_lenh):
        if ma_lenh != self.phieu_can_hien_tai.get('Mã lệnh'):
            self.update_status_signal.emit("Xác nhận thất bại! Sai mã lệnh.", "red")
            self.reset_process()
            return
            
        self.update_status_signal.emit("Đang lưu phiếu cân...", "blue")
        
        self.phieu_can_hien_tai['Trạm cân'] = self._config.get('location_label.name', 'N/A')
        
        is_update = self.phieu_can_hien_tai.get('Id') is not None
        
        table_info = self._config.get_nocodb_table_by_name("Lịch sử cân")
        if not table_info:
            self.update_status_signal.emit("Lỗi cấu hình: Không tìm thấy bảng 'Lịch sử cân'.", "red")
            return
        table_id = table_info.get('id')

        if is_update:
            self._repo.complete_phieu_can_local(self.phieu_can_hien_tai)
            _, error = self._repo.update_phieu_can_api(table_id, self.phieu_can_hien_tai)
        else:
            self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
            response, error = self._repo.create_phieu_can_api(table_id, self.phieu_can_hien_tai)
            if response and 'Id' in response:
                self.phieu_can_hien_tai['Id'] = response.get('Id')
                self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)

        if error:
            self.update_status_signal.emit(f"Lưu phiếu cân thất bại: {error}", "red")
        else:
            self.update_status_signal.emit("Lưu phiếu cân thành công!", "green")
            
        QTimer.singleShot(3000, self.reset_process)

    def _build_weighing_ticket(self, lenh_can, lai_xe, phuong_tien, phieu_can_cho):
        if phieu_can_cho:
            phieu_can_cho.update({
                'Tên hàng hoá': lenh_can.get('Tên hàng hoá', phieu_can_cho.get('Tên hàng hoá')),
                'Tên gọi tắt': phuong_tien.get('Tên gọi tắt', phieu_can_cho.get('Tên gọi tắt')),
                'Tự trọng xe (Kg)': phuong_tien.get('Tự trọng xe', phieu_can_cho.get('Tự trọng xe (Kg)')),
                'Đơn vị': lai_xe.get('Đơn vị', phieu_can_cho.get('Đơn vị')),
            })
            return phieu_can_cho
        
        return {
            "Mã lệnh": lenh_can.get('Mã lệnh'), "Biển số": phuong_tien.get('Biển số'),
            "Mã lái xe": lai_xe.get('Mã lái xe'), "Tên hàng hoá": lenh_can.get('Tên hàng hoá', 'N/A'),
            "Tên gọi tắt": phuong_tien.get('Tên gọi tắt', 'N/A'), "Tự trọng xe (Kg)": phuong_tien.get('Tự trọng xe'),
            "Đơn vị": lai_xe.get('Đơn vị'), "Nhập": lenh_can.get('Nhập'), "Xuất": lenh_can.get('Xuất'),
            "Phân loại": lenh_can.get('Phân loại'), "Cân lần 1 (Kg)": None, "Thời gian cân lần 1": None,
            "Cân lần 2 (Kg)": None, "Thời gian cân lần 2": None, "Hàng hoá (Kg)": None,
            "Độ lệch bì (Kg)": None, "Id": None
        }

    def _calculate_final_weight(self):
        w1 = self.phieu_can_hien_tai.get('Cân lần 1 (Kg)')
        w2 = self.phieu_can_hien_tai.get('Cân lần 2 (Kg)')
        tu_trong_xe = self.phieu_can_hien_tai.get('Tự trọng xe (Kg)')
        
        if w1 is None or w2 is None: return
        
        self.phieu_can_hien_tai['Hàng hoá (Kg)'] = abs(w1 - w2)
        
        if tu_trong_xe is not None:
            can_khong_hang = min(w1, w2)
            self.phieu_can_hien_tai['Độ lệch bì (Kg)'] = can_khong_hang - tu_trong_xe
        
    def reset_process(self):
        print("Controller: Resetting process.")
        self.current_state = self.STATE_IDLE
        self.phieu_can_hien_tai = {}
        self.inactivity_timer.stop()
        self.reset_all_steps_signal.emit()
        self.update_status_signal.emit("Sẵn sàng quét mã lệnh.", "black")
        
        mode_desc = self._config.get('scale_mode.description', 'Tự Động')
        self.update_mode_signal.emit(mode_desc)

    def restart_inactivity_timer(self):
        reset_time = self._config.get('reset_time', 15) * 1000
        self.inactivity_timer.start(reset_time)
