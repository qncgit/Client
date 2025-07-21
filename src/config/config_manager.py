import json
import os
from functools import reduce
import operator
# Thay đổi ở đây
from src.utils.helpers import Common

class ConfigManager:
    def __init__(self, config_path='database/config.json'):
        # Thay đổi ở đây
        self.config_path = Common.resource_path(config_path)
        self.config = self._load_config()

    def _load_config(self):
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
        keys = path.split('.')
        try:
            return reduce(operator.getitem, keys, self.config)
        except (KeyError, TypeError, IndexError):
            return default

    def set_all(self, new_config_dict):
        self.config = new_config_dict

    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu file cấu hình: {e}")
            return False
            
    def reload(self):
        self.config = self._load_config()

    def get_nocodb_table_by_name(self, target_name):
        tables = self.get('nocodb.tables', {})
        for table_key, table_info in tables.items():
            if table_info.get('name') == target_name:
                return table_info
        return None

    def get_nocodb_view_by_name(self, table_info, target_view_name):
        if not table_info:
            return None
        views = table_info.get('views', {})
        for view_key, view_info in views.items():
            if view_info.get('name') == target_view_name:
                return view_info
        return None