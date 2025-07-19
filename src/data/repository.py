import json
import os
from .api_client import ApiClient

class Repository:
    """
    Quản lý việc truy cập và thao tác dữ liệu, bao gồm cả file JSON cục bộ
    và dữ liệu từ API. Đây là nguồn dữ liệu duy nhất cho ứng dụng.
    """
    def __init__(self, config_manager, db_path='database/'):
        self.db_path = db_path
        self.api_client = ApiClient(config_manager)
        
        # Cache dữ liệu trong bộ nhớ
        self.lenh_can = []
        self.phuong_tien = []
        self.nhan_vien = []
        self.phieu_can_dang_cho = []
        self.phieu_can_lich_su = []
        
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
        """Tải tất cả dữ liệu từ các file JSON vào bộ nhớ cache."""
        self.lenh_can = self._load_json('Thongtinlenhcan.json')
        self.phuong_tien = self._load_json('Thongtinphuongtien.json')
        self.nhan_vien = self._load_json('Thongtinnhanvien.json')
        self.phieu_can_dang_cho = self._load_json('Dangcan.json')
        self.phieu_can_lich_su = self._load_json('lichsucan.json')
        print("Đã tải dữ liệu cục bộ vào bộ nhớ.")

    # --- Phương thức đồng bộ dữ liệu ---
    def sync_table(self, table_name, table_id, view_id):
        """Hàm chung để đồng bộ một bảng dữ liệu."""
        data, error = self.api_client.get_data(table_id, view_id)
        if data and 'list' in data:
            # Cập nhật cache trong bộ nhớ
            if table_name == 'lenh_can': self.lenh_can = data['list']
            elif table_name == 'phuong_tien': self.phuong_tien = data['list']
            elif table_name == 'nhan_vien': self.nhan_vien = data['list']
            
            # Lưu vào file JSON tương ứng
            filename_map = {
                'lenh_can': 'Thongtinlenhcan.json',
                'phuong_tien': 'Thongtinphuongtien.json',
                'nhan_vien': 'Thongtinnhanvien.json'
            }
            self._save_json(filename_map[table_name], data['list'])
            return True, f"Đồng bộ {table_name} thành công."
        return False, error or f"Không có dữ liệu {table_name}."

    # --- Phương thức truy vấn dữ liệu (từ cache) ---
    def get_lenh_can_by_id(self, ma_lenh):
        # SỬA LỖI: Sử dụng đúng key 'Mã lệnh'
        return next((item for item in self.lenh_can if item.get('Mã lệnh') == ma_lenh), None)

    def get_phuong_tien_by_bks(self, bks):
        # SỬA LỖI: Sử dụng đúng key 'Biển số'
        return next((item for item in self.phuong_tien if item.get('Biển số') == bks), None)

    def get_nhan_vien_by_id(self, ma_nv):
        # SỬA LỖI: Sử dụng đúng key 'Mã lái xe'
        return next((item for item in self.nhan_vien if item.get('Mã lái xe') == ma_nv), None)
        
    def find_phieu_can_dang_cho(self, ma_lenh):
        # SỬA LỖI: Sử dụng đúng key 'Mã lệnh'
        return next((item for item in self.phieu_can_dang_cho if item.get('Mã lệnh') == ma_lenh), None)

    # --- Phương thức thay đổi dữ liệu ---
    def create_phieu_can_api(self, table_id, data):
        return self.api_client.create_record(table_id, data)

    def update_phieu_can_api(self, table_id, data):
        return self.api_client.update_record(table_id, data['Id'], data)
        
    def save_phieu_can_dang_cho_local(self, phieu_can):
        """Lưu phiếu cân đang chờ vào cache và file JSON."""
        # SỬA LỖI: Sử dụng đúng key 'Mã lệnh'
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != phieu_can.get('Mã lệnh')]
        self.phieu_can_dang_cho.append(phieu_can)
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)

    def complete_phieu_can_local(self, phieu_can_hoan_thanh):
        """Chuyển phiếu cân từ 'đang chờ' sang 'lịch sử'."""
        # SỬA LỖI: Sử dụng đúng key 'Mã lệnh'
        ma_lenh_hoan_thanh = phieu_can_hoan_thanh.get('Mã lệnh')
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != ma_lenh_hoan_thanh]
        self.phieu_can_lich_su.append(phieu_can_hoan_thanh)
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)
        self._save_json('lichsucan.json', self.phieu_can_lich_su)
