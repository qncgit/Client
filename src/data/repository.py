import json
import os
from .api_client import ApiClient
from src.utils.helpers import Common
import time
from datetime import datetime

class Repository:
    def __init__(self, config_manager, db_path='database/'):
        self.db_path = Common.resource_path(db_path)
        self.api_client = ApiClient(config_manager)
        
        self.lenh_can = []
        self.phuong_tien = []
        self.nhan_vien = []
        self.phieu_can_dang_cho = []
        self.phieu_can_lich_su = []
        self.phieu_can_offline = []  # Queue cho phiếu cân chờ đồng bộ
        
        # Đảm bảo thư mục cơ sở dữ liệu tồn tại
        os.makedirs(self.db_path, exist_ok=True)
        
        self.load_all_local_data()

    def _load_json(self, filename):
        path = os.path.join(self.db_path, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, filename, data):
        path = os.path.join(self.db_path, filename)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Không thể lưu file {filename}: {e}")
            return False

    def load_all_local_data(self):
        self.lenh_can = self._load_json('Thongtinlenhcan.json')
        self.phuong_tien = self._load_json('Thongtinphuongtien.json')
        self.nhan_vien = self._load_json('Thongtinnhanvien.json')
        self.phieu_can_dang_cho = self._load_json('Dangcan.json')
        self.phieu_can_lich_su = self._load_json('lichsucan.json')
        self.phieu_can_offline = self._load_json('offline_queue.json')  # Thêm đọc queue offline

    def sync_table(self, table_name, table_id, view_id):
        data, error = self.api_client.get_data(table_id, view_id)
        if data is not None:
            local_data = []
            if table_name == 'lenh_can': local_data = self.lenh_can
            elif table_name == 'phuong_tien': local_data = self.phuong_tien
            elif table_name == 'nhan_vien': local_data = self.nhan_vien
            elif table_name == 'phieu_can_dang_cho': local_data = self.phieu_can_dang_cho  # Thêm dòng này

            def key_func(item):
                if table_name == 'lenh_can': return item.get('Mã lệnh')
                if table_name == 'phuong_tien': return item.get('Biển số')
                if table_name == 'nhan_vien': return item.get('Mã lái xe')
                if table_name == 'phieu_can_dang_cho': return item.get('Mã lệnh')  # Thêm dòng này
                return None

            merged = {key_func(item): item for item in data if key_func(item) is not None}
            for item in local_data:
                k = key_func(item)
                if k not in merged:
                    merged[k] = item
            merged_list = list(merged.values())

            if table_name == 'lenh_can': self.lenh_can = merged_list
            elif table_name == 'phuong_tien': self.phuong_tien = merged_list
            elif table_name == 'nhan_vien': self.nhan_vien = merged_list
            elif table_name == 'phieu_can_dang_cho': self.phieu_can_dang_cho = merged_list  # Thêm dòng này

            filename_map = {
                'lenh_can': 'Thongtinlenhcan.json',
                'phuong_tien': 'Thongtinphuongtien.json',
                'nhan_vien': 'Thongtinnhanvien.json',
                'phieu_can_dang_cho': 'Dangcan.json'  # Thêm dòng này
            }
            self._save_json(filename_map[table_name], merged_list)
            return True, f"Đồng bộ {table_name} thành công."
        return False, error or f"Không có dữ liệu {table_name}."

    def get_lenh_can_by_id(self, ma_lenh):
        return next((item for item in self.lenh_can if item.get('Mã lệnh') == ma_lenh), None)

    def get_phuong_tien_by_bks(self, bks):
        return next((item for item in self.phuong_tien if item.get('Biển số') == bks), None)

    def get_nhan_vien_by_id(self, ma_nv):
        # So sánh với Label_Mã lái xe thay vì Mã lái xe
        return next((item for item in self.nhan_vien if item.get('Label_Mã lái xe') == ma_nv), None)
        
    def find_phieu_can_dang_cho(self, ma_lenh):
        """Tìm phiếu cân đang chờ theo mã lệnh"""
        # Tìm trong phiếu cân đang chờ trước
        for item in self.phieu_can_dang_cho:
            if item.get('Mã lệnh') == ma_lenh:
                return item
                
        # Nếu không tìm thấy, kiểm tra trong lịch sử cân lần 1 đã được lưu
        for item in self.phieu_can_lich_su:
            if item.get('Mã lệnh') == ma_lenh and item.get('Cân lần 1 (Kg)') is not None and item.get('Cân lần 2 (Kg)') is None:
                return item
                
        return None
        
    def create_phieu_can_api(self, table_id, data):
        """Tạo phiếu cân mới và xử lý trường hợp offline"""
        # Lưu local trước
        self.save_phieu_can_dang_cho_local(data)
        
        # Thử gửi lên API
        response, error = self.api_client.create_record(table_id, data)
        
        if error:
            # Nếu có lỗi, thêm vào queue offline
            self._add_to_offline_queue('create', table_id, data)
            return None, error
        return response, None

    def update_phieu_can_api(self, table_id, data):
        """Cập nhật phiếu cân và xử lý trường hợp offline"""
        # Lưu local trước
        self.complete_phieu_can_local(data)
        
        # Thử gửi lên API
        response, error = self.api_client.update_record(table_id, data)
        
        if error:
            # Nếu có lỗi, thêm vào queue offline
            self._add_to_offline_queue('update', table_id, data)
            return None, error
        return response, None

    def _add_to_offline_queue(self, action_type, table_id, data):
        """Thêm một thao tác vào queue để đồng bộ sau"""
        queue_item = {
            'action': action_type,
            'table_id': table_id,
            'data': data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.phieu_can_offline.append(queue_item)
        self._save_json('offline_queue.json', self.phieu_can_offline)

    def sync_offline_queue(self):
        """Đồng bộ các phiếu cân trong queue offline lên server"""
        if not self.phieu_can_offline:
            return 0, 0  # Không có gì để đồng bộ
        
        success_count = 0
        total = len(self.phieu_can_offline)
        items_to_remove = []
        
        for i, item in enumerate(self.phieu_can_offline):
            try:
                if item['action'] == 'create':
                    response, error = self.api_client.create_record(item['table_id'], item['data'])
                elif item['action'] == 'update':
                    response, error = self.api_client.update_record(item['table_id'], item['data'])
                else:
                    error = "Loại hành động không được hỗ trợ"
                    
                if error is None:
                    success_count += 1
                    items_to_remove.append(i)
                    # Nếu ID phản hồi khác với ID hiện tại, cập nhật trong lịch sử
                    if response and 'Id' in response and item['action'] == 'create':
                        self._update_record_id_in_history(item['data']['Phiếu cân'], response['Id'])
                
            except Exception as e:
                print(f"Lỗi khi đồng bộ queue offline: {e}")
                
        # Loại bỏ các mục đã đồng bộ thành công
        for index in sorted(items_to_remove, reverse=True):
            del self.phieu_can_offline[index]
            
        # Lưu lại queue đã được cập nhật
        self._save_json('offline_queue.json', self.phieu_can_offline)
        
        return success_count, total

    def _update_record_id_in_history(self, old_id, new_id):
        """Cập nhật ID trong lịch sử phiếu cân"""
        for i, record in enumerate(self.phieu_can_lich_su):
            if record.get('Phiếu cân') == old_id:
                self.phieu_can_lich_su[i]['Id'] = new_id
                
        # Lưu lại lịch sử đã cập nhật
        self._save_json('lichsucan.json', self.phieu_can_lich_su)

    def save_phieu_can_dang_cho_local(self, phieu_can):
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != phieu_can.get('Mã lệnh')]
        self.phieu_can_dang_cho.append(phieu_can)
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)

    def complete_phieu_can_local(self, phieu_can_hoan_thanh):
        """Hoàn thành một phiếu cân, chuyển từ đang chờ sang lịch sử"""
        ma_lenh_hoan_thanh = phieu_can_hoan_thanh.get('Mã lệnh')
        # Xóa khỏi danh sách đang chờ nếu có
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != ma_lenh_hoan_thanh]
        
        # Xóa phiếu cân cũ trong lịch sử nếu có (tránh trùng lặp)
        phieu_can_id = phieu_can_hoan_thanh.get('Phiếu cân')
        self.phieu_can_lich_su = [p for p in self.phieu_can_lich_su 
                                  if not (p.get('Mã lệnh') == ma_lenh_hoan_thanh and
                                          p.get('Cân lần 2 (Kg)') is None)]
        
        # Thêm phiếu cân mới vào lịch sử
        self.phieu_can_lich_su.append(phieu_can_hoan_thanh)
        
        # Lưu các file JSON
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)
        self._save_json('lichsucan.json', self.phieu_can_lich_su)

    def get_offline_queue_count(self):
        """Lấy số lượng phiếu cân đang chờ đồng bộ"""
        return len(self.phieu_can_offline)

    def debug_network_status(self):
        """Kiểm tra và ghi log trạng thái kết nối"""
        status, message = self.api_client.check_server_status()
        print(f"DEBUG - Network Status Check: {'ONLINE' if status else 'OFFLINE'}")
        print(f"DEBUG - Status Message: {message}")
        print(f"DEBUG - ApiClient.online: {self.api_client.online}")
        return status