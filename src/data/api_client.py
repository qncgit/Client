import requests
import json

class ApiClient:
    """
    Client để thực hiện các yêu cầu tới NocoDB API v2.
    Đã được cập nhật để khớp với mã nguồn mẫu và cấu trúc config.json.
    """
    def __init__(self, config_manager):
        self._config = config_manager

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
            error_msg = f"Lỗi get_data: {str(e)}"
            print(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Lỗi không xác định trong get_data: {str(e)}"
            print(error_msg)
            return None, error_msg

    def create_record(self, table_id, data):
        """Tạo một bản ghi mới trong bảng."""
        try:
            token = self._config.get('server.api_token', '')
            endpoint = f"api/v2/tables/{table_id}/records"
            url = self._prepare_url(endpoint)
            headers = {'xc-token': token}
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            error_msg = f"Lỗi khi gửi dữ liệu (post): {str(e)}"
            print(error_msg)
            return None, error_msg

    def update_record(self, table_id, data):
        """Cập nhật một bản ghi đã có."""
        try:
            token = self._config.get('server.api_token', '')
            endpoint = f"api/v2/tables/{table_id}/records"
            url = self._prepare_url(endpoint)
            headers = {'xc-token': token}
            
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json(), None
        except requests.exceptions.RequestException as e:
            error_msg = f"Lỗi khi cập nhật dữ liệu (patch): {str(e)}"
            print(error_msg)
            return None, error_msg
