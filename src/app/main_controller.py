from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime
import uuid

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
    weighing_complete_signal = pyqtSignal()
    network_status_changed = pyqtSignal(bool)  # Thêm tín hiệu mới
    
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
        self.is_offline = True  # Mặc định là offline cho đến khi xác nhận trạng thái

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.reset_process)

    def set_current_weight(self, weight):
        self.current_weight = weight

    def set_network_status(self, is_online):
        """Cập nhật trạng thái mạng"""
        old_status = not self.is_offline
        self.is_offline = not is_online
        if old_status != is_online:
            self.network_status_changed.emit(is_online)
            
            # Update UI status immediately when network status changes
            if is_online:
                self.update_status_signal.emit("Sẵn sàng quét mã lệnh.", "green")
            else:
                self.update_status_signal.emit("Sẵn sàng quét mã lệnh (chế độ offline).", "orange")

    def handle_qr_scan(self, qr_data):
        self.restart_inactivity_timer()
        
        parts = qr_data.strip().split('_')
        if len(parts) < 3:
            self.update_status_signal.emit(f"Lỗi mã QR: Sai cấu trúc. ({qr_data})", "red")
            return
            
        ma_lenh = parts[0]
        ma_lai_xe = parts[1]
        bien_so_xe = parts[2]
        
        # Hỗ trợ QR mở rộng với thông tin bổ sung (cho chế độ offline)
        additional_data = {}
        if len(parts) > 3:
            try:
                # Hỗ trợ các thông tin bổ sung theo format:
                # tenhang|phanloai|nhap|xuat|khochua
                additional_data['Tên hàng hoá'] = parts[3] if len(parts) > 3 else None
                additional_data['Phân loại'] = parts[4] if len(parts) > 4 else None
                additional_data['Nhập'] = parts[5] if len(parts) > 5 else None
                additional_data['Xuất'] = parts[6] if len(parts) > 6 else None
                additional_data['Tên kho chứa'] = parts[7] if len(parts) > 7 else None
            except:
                pass
        
        if self.current_state == self.STATE_IDLE:
            self._handle_new_weighing_request(ma_lenh, ma_lai_xe, bien_so_xe, additional_data)
        elif self.current_state == self.STATE_WAITING_CONFIRM:
            # Chỉ xác nhận lưu nếu mã lệnh trùng với phiếu cân hiện tại
            if ma_lenh == self.phieu_can_hien_tai.get('Mã lệnh'):
                self._handle_save_confirmation(ma_lenh)
            else:
                self.update_status_signal.emit("Mã QR xác nhận không khớp với phiếu cân đang chờ!", "red")
        else:
            self.update_status_signal.emit("Hệ thống đang xử lý, vui lòng chờ.", "orange")

    def _handle_new_weighing_request(self, ma_lenh, ma_lai_xe, bien_so_xe, additional_data=None):
        self.current_state = self.STATE_PROCESSING
        self.update_status_signal.emit(f"Đã nhận lệnh '{ma_lenh}'. Đưa xe vào vị trí cân ổn định.", "blue")
        
        # Lấy dữ liệu từ local cache
        lenh_can_details = self._repo.get_lenh_can_by_id(ma_lenh)
        lai_xe_details = self._repo.get_nhan_vien_by_id(ma_lai_xe)
        phuong_tien_details = self._repo.get_phuong_tien_by_bks(bien_so_xe)
        
        # Nếu trong chế độ offline và không tìm thấy dữ liệu, sử dụng dữ liệu từ QR
        if self.is_offline:
            # Tạo thông tin lệnh cân từ QR nếu không có trong cache
            if not lenh_can_details:
                lenh_can_details = {
                    'Mã lệnh': ma_lenh,
                    'KetQua': '<span style="color: orange; font-weight: bold;">OFFLINE</span>',
                }
                # Bổ sung thông tin từ QR mở rộng nếu có
                if additional_data:
                    for key, value in additional_data.items():
                        if value:
                            lenh_can_details[key] = value
            
            # Tạo thông tin lái xe từ QR nếu không có trong cache
            if not lai_xe_details:
                lai_xe_details = {
                    'Mã lái xe': ma_lai_xe,
                    'Họ và tên': ma_lai_xe,
                    'KetQua': '<span style="color: orange; font-weight: bold;">OFFLINE</span>',
                }
            
            # Tạo thông tin phương tiện từ QR nếu không có trong cache
            if not phuong_tien_details:
                phuong_tien_details = {
                    'Biển số': bien_so_xe,
                    'Tự trọng xe': 0,  # Giả định tự trọng = 0 nếu không có dữ liệu
                    'KetQua': '<span style="color: orange; font-weight: bold;">OFFLINE</span>',
                }

        # Tiếp tục xử lý như bình thường
        lenh_can_info = lenh_can_details if lenh_can_details else {'Mã lệnh': ma_lenh}
        lenh_can_info['KetQua'] = lenh_can_info.get('KetQua', "THÀNH CÔNG" if lenh_can_details else "KHÔNG TÌM THẤY")

        lai_xe_info = lai_xe_details if lai_xe_details else {'Mã lái xe': ma_lai_xe, 'Họ và tên': ma_lai_xe}
        lai_xe_info['KetQua'] = lai_xe_info.get('KetQua', "THÀNH CÔNG" if lai_xe_details else "KHÔNG TÌM THẤY")

        phuong_tien_info = phuong_tien_details if phuong_tien_details else {'Biển số': bien_so_xe}
        phuong_tien_info['KetQua'] = phuong_tien_info.get('KetQua', "THÀNH CÔNG" if phuong_tien_details else "KHÔNG TÌM THẤY")

        # Phân biệt cân lần đầu và cân lần hai
        phieu_can_cho = self._repo.find_phieu_can_dang_cho(ma_lenh)
        if phieu_can_cho:
            # Nếu đã có phiếu cân (cân lần 2), lấy phiếu cân từ json
            self.phieu_can_hien_tai = self._build_weighing_ticket(
                lenh_can_info, lai_xe_info, phuong_tien_info, phieu_can_cho
            )
            # Sử dụng đúng UUID đã lưu
            self.phieu_can_hien_tai['Phiếu cân'] = str(phieu_can_cho.get('Phiếu cân', phieu_can_cho.get('Id', '')))
            if 'Id' not in self.phieu_can_hien_tai or not self.phieu_can_hien_tai['Id']:
                self.phieu_can_hien_tai['Id'] = self.phieu_can_hien_tai['Phiếu cân']
        else:
            # Nếu chưa có phiếu cân (cân lần đầu), tạo mới phiếu cân với UUID4
            uuid_str = str(uuid.uuid4())
            self.phieu_can_hien_tai = self._build_weighing_ticket(
                lenh_can_info, lai_xe_info, phuong_tien_info, None
            )
            self.phieu_can_hien_tai['Phiếu cân'] = uuid_str
            self.phieu_can_hien_tai['Id'] = uuid_str

        # Đánh dấu chế độ offline nếu đang offline
        if self.is_offline:
            self.phieu_can_hien_tai['TRANGTHAI'] = '<span style="color: orange; font-weight: bold;">OFFLINE</span>'
        else:
            self.phieu_can_hien_tai['TRANGTHAI'] = "-"

        self.update_step1_signal.emit(lenh_can_info)
        self.update_step2_signal.emit(lai_xe_info)
        self.update_step3_signal.emit(phuong_tien_info)
        self.update_step4_signal.emit(self.phieu_can_hien_tai)
        
        stable_time = self._config.get('app.stable_time', 3)
        QTimer.singleShot(stable_time * 1000, self._execute_weighing)

    def _execute_weighing(self):
        mode = self._config.get('scale_mode.type', 'auto')
        
        if self.phieu_can_hien_tai.get('Cân lần 1 (Kg)') is None and mode in ['auto', 'in']:
            self.phieu_can_hien_tai['Cân lần 1 (Kg)'] = self.current_weight
            self.phieu_can_hien_tai['Thời gian cân lần 1'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            self.update_status_signal.emit("Đã ghi nhận cân lần 1. Quét lại mã QR để xác nhận lưu.", "green")
            self.current_state = self.STATE_WAITING_CONFIRM  # Cập nhật trạng thái
        elif self.phieu_can_hien_tai.get('Cân lần 1 (Kg)') is not None and mode in ['auto', 'out']:
            self.phieu_can_hien_tai['Cân lần 2 (Kg)'] = self.current_weight
            self.phieu_can_hien_tai['Thời gian cân lần 2'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            self._calculate_final_weight()
            self.update_status_signal.emit("Đã ghi nhận cân lần 2. Quét lại mã QR để xác nhận lưu.", "green")
            self.current_state = self.STATE_WAITING_CONFIRM  # Cập nhật trạng thái
        else:
            self.update_status_signal.emit(f"Chế độ '{mode}' không cho phép thực hiện thao tác này.", "red")
            self.reset_process()
            return

        # Sau khi cân xong, cập nhật trạng thái phiếu cân
        self.phieu_can_hien_tai['TRANGTHAI'] = '<span style="color: orange; font-weight: bold;">VUI LÒNG QUÉT LẠI MÃ QR ĐỂ XÁC THỰC LƯU</span>'
        self.update_step4_signal.emit(self.phieu_can_hien_tai)
        self.weighing_complete_signal.emit()  # Phát tín hiệu cân xong
        self.restart_inactivity_timer()

    def _handle_save_confirmation(self, ma_lenh):
        if ma_lenh != self.phieu_can_hien_tai.get('Mã lệnh'):
            self.phieu_can_hien_tai['TRANGTHAI'] = "XÁC NHẬN THẤT BẠI"
            self.update_step4_signal.emit(self.phieu_can_hien_tai)
            self.update_status_signal.emit("Xác nhận thất bại! Sai mã lệnh.", "red")
            # Không reset form ngay, để người dùng nhìn thấy thông báo lỗi
            # self.reset_process()
            return
            
        if self.is_offline:
            self.update_status_signal.emit("Đang lưu phiếu cân (chế độ offline)...", "blue")
        else:
            self.update_status_signal.emit("Đang lưu phiếu cân...", "blue")
            
        self.phieu_can_hien_tai['TRANGTHAI'] = "ĐANG LƯU"
        self.update_step4_signal.emit(self.phieu_can_hien_tai)
        
        self.phieu_can_hien_tai['Trạm cân'] = self._config.get('location_label.name', 'N/A')
        
        is_update = self.phieu_can_hien_tai.get('Cân lần 2 (Kg)') is not None
        
        table_info = self._config.get_nocodb_table_by_name("Lịch sử cân")
        if not table_info:
            self.update_status_signal.emit("Lỗi cấu hình: Không tìm thấy bảng 'Lịch sử cân'.", "red")
            self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
            self.update_status_signal.emit("Phiếu cân đã được lưu offline.", "orange")
            # Không reset form ngay, để người dùng thấy thông báo
            return
        table_id = table_info.get('id')

        # Luôn lưu local trước, sau đó gửi lên server
        if is_update:
            # Phiếu đã hoàn thành cả 2 lần cân, lưu vào lịch sử
            self._repo.complete_phieu_can_local(self.phieu_can_hien_tai)
            if not self.is_offline:
                _, error = self._repo.update_phieu_can_api(table_id, self.phieu_can_hien_tai)
            else:
                # Khi offline, đánh dấu lỗi để tự động thêm vào queue
                error = "Đang trong chế độ offline"
        else:
            # Phiếu mới cân lần 1, lưu vào phiếu đang chờ
            self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
            if not self.is_offline:
                response, error = self._repo.create_phieu_can_api(table_id, self.phieu_can_hien_tai)
                if response and 'Id' in response:
                    self.phieu_can_hien_tai['Id'] = response.get('Id')
                    # Cập nhật lại ID trong danh sách đang chờ
                    self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
            else:
                # Khi offline, đánh dấu lỗi để tự động thêm vào queue
                error = "Đang trong chế độ offline"

        if error:
            if self.is_offline:
                self.phieu_can_hien_tai['TRANGTHAI'] = '<span style="color: green; font-weight: bold;">LƯU THÀNH CÔNG</span>'
                self.phieu_can_hien_tai['KetQua'] = "HOÀN THÀNH"
                self.update_step4_signal.emit(self.phieu_can_hien_tai)
                self.update_status_signal.emit("Phiếu cân đã được lưu offline. Sẽ tự động đồng bộ khi có mạng.", "orange")
            else:
                self.phieu_can_hien_tai['TRANGTHAI'] = '<span style="color: green; font-weight: bold;">LƯU THÀNH CÔNG</span>'
                self.phieu_can_hien_tai['KetQua'] = "THẤT BẠI"
                self.update_step4_signal.emit(self.phieu_can_hien_tai)
                self.update_status_signal.emit(f"Lưu phiếu cân thất bại (offline): {error}", "orange")
                self.update_status_signal.emit("Phiếu cân đã được lưu offline. Sẽ tự động đồng bộ khi có mạng.", "orange")
            
            # Không cần lưu lại nếu đã hoàn thành cả 2 lần cân vì đã lưu ở trên
            if not is_update:
                self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
        else:
            self.phieu_can_hien_tai['TRANGTHAI'] = "THÀNH CÔNG"
            self.phieu_can_hien_tai['KetQua'] = "THÀNH CÔNG"
            if self.phieu_can_hien_tai.get('Id'):
                self.phieu_can_hien_tai['Phiếu cân'] = str(self.phieu_can_hien_tai['Id'])
            self.update_step4_signal.emit(self.phieu_can_hien_tai)
            self.update_status_signal.emit("Lưu phiếu cân thành công!", "green")
            
            # Nếu chỉ mới cân lần 1, vẫn cần lưu vào danh sách đang chờ
            if not is_update:
                self._repo.save_phieu_can_dang_cho_local(self.phieu_can_hien_tai)
            # Tiếp tục đếm ngược đến khi hết thời gian, không reset ngay
            
        # Đặt trạng thái về IDLE để chuẩn bị quét mã mới sau khi đếm ngược hết
        self.current_state = self.STATE_IDLE
        
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
        
        # Remove the offline check here since we already update status when network status changes
        self.update_status_signal.emit("Sẵn sàng quét mã lệnh.", "green" if not self.is_offline else "orange")
        if self.is_offline:
            self.update_status_signal.emit("Sẵn sàng quét mã lệnh (chế độ offline).", "orange")
        
        mode_desc = self._config.get('scale_mode.description', 'Tự Động')
        self.update_mode_signal.emit(mode_desc)

    def restart_inactivity_timer(self):
        reset_time = self._config.get('reset_time', 15) * 1000
        self.inactivity_timer.start(reset_time)
