import hashlib
import os
import sys

class Common:
    @staticmethod
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
    
        return os.path.join(base_path, relative_path)
    
    @staticmethod
    def hash_password(password: str) -> str:
        if not isinstance(password, str):
            return ""
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return sha256.hexdigest()