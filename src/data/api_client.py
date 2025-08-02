import requests
import json
import socket

class ApiClient:
    """
    Client để thực hiện các yêu cầu tới NocoDB API v2.
    Đã được cập nhật để khớp với mã nguồn mẫu và cấu trúc config.json.
    """
    def __init__(self, config_manager):
        self._config = config_manager
        self.online = False
        self._check_connection()

    def _check_connection(self):
        """Kiểm tra kết nối đến server"""
        status, _ = self.check_server_status()
        self.online = status
        return status

    def _prepare_url(self, endpoint):
        """
        Chuẩn bị URL hoàn chỉnh, đảm bảo có giao thức http.
        """
        host = self._config.get('server.host', 'localhost')
        port = self._config.get('server.port', 8080)
        
        # Đảm bảo host luôn có scheme http://
        if not host.startswith('http://') and not host.startswith('https://'):
            host = f"http://{host}"
            
        return f"{host}:{port}/{endpoint}"

    def get_data(self, table_id, view_id):
        """
        Lấy toàn bộ dữ liệu từ một view, xử lý pagination.
        """
        # Kiểm tra kết nối đến server trước
        if not self._check_connection():
            return None, "Không thể kết nối đến máy chủ"
            
        try:
            token = self._config.get('server.api_token', '')
            endpoint = f"api/v2/tables/{table_id}/records"
            url = self._prepare_url(endpoint)
            headers = {'xc-token': token}
            
            all_records = []
            offset = 0
            limit = 100 # Lấy 100 bản ghi mỗi lần để tăng tốc độ

            while True:
                querystring = {
                    "offset": str(offset),
                    "limit": str(limit),
                    "viewId": view_id
                }
                response = requests.get(url, headers=headers, params=querystring, timeout=15)
                response.raise_for_status()
                
                records = response.json().get('list', [])
                all_records.extend(records)
                
                if len(records) < limit:
                    break # Đã lấy hết dữ liệu
                offset += limit
            
            return all_records, None
        except requests.exceptions.RequestException as e:
            self.online = False
            error_msg = f"Lỗi get_data: {str(e)}"
            print(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Lỗi không xác định trong get_data: {str(e)}"
            print(error_msg)
            return None, error_msg

    def create_record(self, table_id, data):
        """Tạo một bản ghi mới trong bảng."""
        # Kiểm tra kết nối đến server trước
        if not self._check_connection():
            return None, "Không thể kết nối đến máy chủ"
            
        try:
            token = self._config.get('server.api_token', '')
            endpoint = f"api/v2/tables/{table_id}/records"
            url = self._prepare_url(endpoint)
            headers = {'xc-token': token}
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            self.online = False
            error_msg = f"Lỗi khi gửi dữ liệu (post): {str(e)}"
            print(error_msg)
            return None, error_msg

    def update_record(self, table_id, data):
        """Cập nhật một bản ghi đã có."""
        # Kiểm tra kết nối đến server trước
        if not self._check_connection():
            return None, "Không thể kết nối đến máy chủ"
            
        try:
            token = self._config.get('server.api_token', '')
            endpoint = f"api/v2/tables/{table_id}/records"
            url = self._prepare_url(endpoint)
            headers = {'xc-token': token}
            
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            self.online = False
            error_msg = f"Lỗi khi cập nhật dữ liệu (patch): {str(e)}"
            print(error_msg)
            return None, error_msg
            
    def check_server_status(self):
        """Kiểm tra trạng thái kết nối với máy chủ"""
        try:
            host = self._config.get('server.host', 'localhost')
            port = self._config.get('server.port', 8888)
            
            # Nếu host chỉ là IP hoặc tên miền (không có http(s)), thêm vào
            if not host.startswith('http://') and not host.startswith('https://'):
                host = f"http://{host}"
                
            url = f"{host}:{port}/dashboard"
            
            # Thử kết nối đến server
            response = requests.get(url, timeout=5)
            
            # Kiểm tra xem phản hồi có phải là một trang web/giao diện hợp lệ không
            if response.status_code == 200:
                self.online = True
                print(f"API check: Server connection successful - {url}")
                return True, "Kết nối máy chủ thành công"
            else:
                self.online = False
                print(f"API check: Server responded with error code: {response.status_code} - {url}")
                return False, f"Máy chủ phản hồi mã lỗi: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            self.online = False
            print(f"API check: Cannot connect to server: {str(e)}")
            return False, f"Không thể kết nối đến máy chủ: {str(e)}"
            if response.status_code == 200:
                self.online = True
                print(f"API check: Server connection successful - {url}")
                return True, "Kết nối máy chủ thành công"
            else:
                self.online = False
                print(f"API check: Server responded with error code: {response.status_code} - {url}")
                return False, f"Máy chủ phản hồi mã lỗi: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            self.online = False
            print(f"API check: Cannot connect to server: {str(e)}")
            return False, f"Không thể kết nối đến máy chủ: {str(e)}"
