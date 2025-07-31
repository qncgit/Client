import json
import os
from .api_client import ApiClient
# Thay đổi ở đây
from src.utils.helpers import Common

class Repository:
    def __init__(self, config_manager, db_path='database/'):
        # Thay đổi ở đây
        self.db_path = Common.resource_path(db_path)
        self.api_client = ApiClient(config_manager)
        
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
        self.lenh_can = self._load_json('Thongtinlenhcan.json')
        self.phuong_tien = self._load_json('Thongtinphuongtien.json')
        self.nhan_vien = self._load_json('Thongtinnhanvien.json')
        self.phieu_can_dang_cho = self._load_json('Dangcan.json')
        self.phieu_can_lich_su = self._load_json('lichsucan.json')

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
        return next((item for item in self.phieu_can_dang_cho if item.get('Mã lệnh') == ma_lenh), None)

    def create_phieu_can_api(self, table_id, data):
        self.save_phieu_can_dang_cho_local(data)
        return self.api_client.create_record(table_id, data)

    def update_phieu_can_api(self, table_id, data):
        self.complete_phieu_can_local(data)
        return self.api_client.update_record(table_id, data)

    def save_phieu_can_dang_cho_local(self, phieu_can):
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != phieu_can.get('Mã lệnh')]
        self.phieu_can_dang_cho.append(phieu_can)
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)

    def complete_phieu_can_local(self, phieu_can_hoan_thanh):
        ma_lenh_hoan_thanh = phieu_can_hoan_thanh.get('Mã lệnh')
        self.phieu_can_dang_cho = [p for p in self.phieu_can_dang_cho if p.get('Mã lệnh') != ma_lenh_hoan_thanh]
        self.phieu_can_lich_su.append(phieu_can_hoan_thanh)
        self._save_json('Dangcan.json', self.phieu_can_dang_cho)
        self._save_json('lichsucan.json', self.phieu_can_lich_su)