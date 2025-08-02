from PyQt5.QtCore import QThread, pyqtSignal
import time
import datetime

class SyncThread(QThread):
    """
    Luồng chạy nền để đồng bộ dữ liệu từ API về máy trạm theo định kỳ.
    """
    sync_status_update = pyqtSignal(str, bool) # message, is_success
    offline_sync_status = pyqtSignal(str, int) # message, pending_count
    network_status_update = pyqtSignal(bool) # online status

    def __init__(self, repository, config_manager):
        super().__init__()
        self._repository = repository
        self._config = config_manager
        self._is_running = False
        self._last_network_status = False

    def run(self):
        self._is_running = True
        
        # Ánh xạ tên bảng trong config sang tên file JSON
        self.table_map = {
            "Thông tin nhân viên": "nhan_vien",
            "Thông tin phương tiện": "phuong_tien",
            "Thông tin lệnh cân": "lenh_can",
            "Lịch sử cân": "phieu_can_dang_cho"
        }
        self.view_map = {
            "Thông tin nhân viên": "Thongtinnhanvien",
            "Thông tin phương tiện": "Thongtinphuongtien",
            "Thông tin lệnh cân": "Thongtinlenhcan",
            "Lịch sử cân": "Dangcan"
        }

        # Đảm bảo kiểm tra kết nối ngay khi khởi động
        self._check_network_status()

        while self._is_running:
            sync_interval = self._config.get('server.sync_interval', 60)
            
            # Kiểm tra trạng thái mạng và cập nhật nếu có thay đổi
            self._check_network_status()
                
            if self._last_network_status:
                print(f"Bắt đầu chu kỳ đồng bộ dữ liệu (lặp lại sau {sync_interval}s)...")
                
                # Đồng bộ queue offline nếu có kết nối
                offline_count = self._repository.get_offline_queue_count()
                if offline_count > 0:
                    success_count, total = self._repository.sync_offline_queue()
                    remaining = total - success_count
                    
                    if success_count > 0:
                        self.offline_sync_status.emit(
                            f"Đã đồng bộ {success_count}/{total} phiếu cân đang chờ", 
                            remaining
                        )
                    
                all_success = True
                tables_to_sync = self._config.get('nocodb.tables', {})

                for table_key, table_config in tables_to_sync.items():
                    if not self._is_running: break
                    
                    table_name_from_config = table_config.get('name')
                    internal_name = self.table_map.get(table_name_from_config)
                    
                    if not internal_name:
                        continue

                    target_view_name = self.view_map.get(table_name_from_config)
                    view_info = self._config.get_nocodb_view_by_name(table_config, target_view_name)
                    
                    if table_config.get('id') and view_info and view_info.get('id'):
                        table_id = table_config['id']
                        view_id = view_info['id']
                        success, message = self._repository.sync_table(internal_name, table_id, view_id)
                        self.sync_status_update.emit(message, success)
                        if not success:
                            all_success = False
                    else:
                        msg = f"Bỏ qua đồng bộ '{table_name_from_config}': thiếu config ID."
                        self.sync_status_update.emit(msg, False)
                        print(msg)

                if all_success:
                    self.sync_status_update.emit("Đồng bộ thành công.", True)
                else:
                    self.sync_status_update.emit("Đồng bộ thất bại.", False)
            else:
                # Thông báo đang trong chế độ offline
                offline_count = self._repository.get_offline_queue_count()
                if offline_count > 0:
                    self.offline_sync_status.emit(f"Đang trong chế độ offline ({offline_count} phiếu chờ đồng bộ)", offline_count)
                else:
                    self.offline_sync_status.emit("Đang trong chế độ offline", 0)

            for _ in range(sync_interval):
                if not self._is_running:
                    break
                time.sleep(1)
                # Kiểm tra trạng thái mạng mỗi 10 giây
                if _ % 10 == 0 and self._is_running:
                    self._check_network_status()

        print("Luồng đồng bộ đã dừng.")
            
    def _check_network_status(self):
        """Kiểm tra trạng thái mạng và cập nhật nếu có thay đổi"""
        try:
            current_network_status, message = self._repository.api_client.check_server_status()
            
            # Chỉ cập nhật trạng thái khi có sự thay đổi
            if current_network_status != self._last_network_status:
                self._last_network_status = current_network_status
                self.network_status_update.emit(current_network_status)
                status_text = "ONLINE" if current_network_status else "OFFLINE"
                print(f"Network status changed to: {status_text} - {message}")
                
                # Đồng thời phát tín hiệu thông báo trạng thái
                self.sync_status_update.emit(message, current_network_status)
                
            return current_network_status
        except Exception as e:
            print(f"Network check error: {str(e)}")
            if self._last_network_status:
                self._last_network_status = False
                self.network_status_update.emit(False)
                self.sync_status_update.emit(f"Lỗi kiểm tra kết nối: {str(e)}", False)
            return False
            
    def stop(self):
        self._is_running = False
        self.wait(2000)
