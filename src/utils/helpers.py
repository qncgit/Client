import hashlib
import os
import sys

class Common:
    @staticmethod
    def resource_path(relative_path):
        try:
            # Khi chạy file .exe
            base_path = sys._MEIPASS
        except Exception:
            # Khi chạy bằng python trực tiếp
            base_path = os.path.abspath(".")
    
        return os.path.join(base_path, relative_path)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Băm mật khẩu bằng thuật toán SHA-256.

        Args:
            password: Mật khẩu dạng chuỗi.

        Returns:
            Chuỗi hex đã được băm.
        """
        if not isinstance(password, str):
            return ""
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return sha256.hexdigest()