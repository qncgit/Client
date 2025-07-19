from PyQt5.QtCore import QThread, pyqtSignal
import serial
import time

class WeightThread(QThread):
    """
    Luồng riêng để đọc dữ liệu trọng lượng từ đầu cân qua cổng serial.
    """
    weight_update = pyqtSignal(int)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, config_manager):
        super().__init__()
        self._config = config_manager
        self.ser = None
        self._is_running = False

    def _initialize_serial(self):
        """Khởi tạo kết nối serial dựa trên cấu hình."""
        try:
            port = self._config.get('scale.com_port', 'COM1')
            baudrate = self._config.get('scale.baud_rate', 4800)
            parity_config = self._config.get('scale.parity', 'N').upper()
            
            parity_map = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD}
            parity = parity_map.get(parity_config, serial.PARITY_NONE)
            
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=self._config.get('scale.stop_bits', 1),
                bytesize=self._config.get('scale.bytesize', 8),
                timeout=self._config.get('scale.timeout', 1)
            )
            self.connection_status.emit(True, f"Đã kết nối tới {port}")
            return True
        except serial.SerialException as e:
            self.connection_status.emit(False, f"Lỗi cổng COM: {e}")
            self.ser = None
            return False

    def run(self):
        self._is_running = True
        
        if not self._initialize_serial():
            while self._is_running and not self.ser:
                time.sleep(5)
                self._initialize_serial()

        buffer = bytearray()
        while self._is_running:
            if not self.ser or not self.ser.is_open:
                time.sleep(1)
                continue
            
            try:
                data = self.ser.read(32)
                if data:
                    buffer.extend(data)
                    
                    while True:
                        start_index = buffer.find(b'\x02')
                        end_index = buffer.find(b'\x03')

                        if start_index != -1 and end_index != -1 and start_index < end_index:
                            frame = buffer[start_index + 1 : end_index]
                            try:
                                weight_str = frame.decode('ascii').strip()
                                weight = int(weight_str)
                                self.weight_update.emit(weight)
                            except (ValueError, UnicodeDecodeError):
                                pass
                            buffer = buffer[end_index + 1:]
                        else:
                            break
                
                if len(buffer) > 256:
                    buffer = bytearray()

            except serial.SerialException:
                self.connection_status.emit(False, "Mất kết nối cổng COM.")
                if self.ser:
                    self.ser.close()
                self.ser = None
                while self._is_running and not self.ser:
                    time.sleep(5)
                    self._initialize_serial()
            
            time.sleep(0.05)

        if self.ser and self.ser.is_open:
            self.ser.close()
        print("Luồng đọc cân đã dừng.")

    def stop(self):
        self._is_running = False
        self.wait(2000)
