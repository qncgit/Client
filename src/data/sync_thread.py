from PyQt5.QtCore import QThread, pyqtSignal
import time

class SyncThread(QThread):
    """
    Luồng chạy nền để đồng bộ dữ liệu từ API về máy trạm theo định kỳ.
    """
    sync_status_update = pyqtSignal(str, bool) # message, is_success

    def __init__(self, repository, config_manager):
        super().__init__()
        self._repository = repository
        self._config = config_manager
        self._is_running = False

    def run(self):
        self._is_running = True
        
        # Ánh xạ tên bảng trong config sang tên file JSON
        self.table_map = {
            "Thông tin nhân viên": "nhan_vien",
            "Thông tin phương tiện": "phuong_tien",
            "Thông tin lệnh cân": "lenh_can"
        }
        self.view_map = {
            "Thông tin nhân viên": "Thongtinnhanvien",
            "Thông tin phương tiện": "Thongtinphuongtien",
            "Thông tin lệnh cân": "Thongtinlenhcan"
        }

        while self._is_running:
            sync_interval = self._config.get('server.sync_interval', 60)
            print(f"Bắt đầu chu kỳ đồng bộ dữ liệu (lặp lại sau {sync_interval}s)...")
            
            all_success = True
            tables_to_sync = self._config.get('nocodb.tables', {})

            for table_key, table_config in tables_to_sync.items():
                if not self._is_running: break
                
                table_name_from_config = table_config.get('name')
                internal_name = self.table_map.get(table_name_from_config)
                
                if not internal_name:
                    continue # Bỏ qua các bảng không cần đồng bộ (vd: Lịch sử cân)

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

            for _ in range(sync_interval):
                if not self._is_running:
                    break
                time.sleep(1)

        print("Luồng đồng bộ đã dừng.")
            
    def stop(self):
        self._is_running = False
        self.wait(2000)
