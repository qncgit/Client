import json
import os
from functools import reduce
import operator

class ConfigManager:
    """
    Quản lý việc đọc, ghi và truy cập các thông số cấu hình
    từ file JSON có cấu trúc lồng nhau (nested).
    """
    def __init__(self, config_path='database/config.json'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Tải cấu hình từ file JSON."""
        if not os.path.exists(self.config_path):
            print(f"Cảnh báo: Không tìm thấy file '{self.config_path}'.")
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Lỗi khi tải file cấu hình: {e}")
            return {}

    def get(self, path, default=None):
        """
        Lấy một giá trị cấu hình theo đường dẫn (ví dụ: 'server.host').
        """
        keys = path.split('.')
        try:
            return reduce(operator.getitem, keys, self.config)
        except (KeyError, TypeError, IndexError):
            return default

    def set_all(self, new_config_dict):
        """Cập nhật toàn bộ cấu hình từ một dictionary."""
        self.config = new_config_dict

    def save_config(self):
        """Lưu cấu hình hiện tại vào file JSON."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu file cấu hình: {e}")
            return False
            
    def reload(self):
        """Tải lại cấu hình từ file."""
        self.config = self._load_config()

    def get_nocodb_table_by_name(self, target_name):
        """Tìm thông tin bảng trong nocodb config bằng tên."""
        tables = self.get('nocodb.tables', {})
        for table_key, table_info in tables.items():
            if table_info.get('name') == target_name:
                return table_info
        return None

    def get_nocodb_view_by_name(self, table_info, target_view_name):
        """Tìm thông tin view trong một bảng bằng tên."""
        if not table_info:
            return None
        views = table_info.get('views', {})
        for view_key, view_info in views.items():
            if view_info.get('name') == target_view_name:
                return view_info
        return None
