from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from src.utils.helpers import hash_password

class VerifiedDialog(QDialog):
    """
    Một cửa sổ dialog đơn giản để yêu cầu người dùng nhập mật khẩu
    và xác thực.
    """
    def __init__(self, correct_hashed_password, parent=None):
        super().__init__(parent)
        self.correct_hashed_password = correct_hashed_password
        
        self.setWindowTitle("Xác thực quyền truy cập")
        self.setModal(True)
        self.setMinimumWidth(300)

        # --- Widgets ---
        self.label = QLabel("Vui lòng nhập mật khẩu quản trị để tiếp tục:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.confirm_button = QPushButton("Xác nhận")
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        # --- Layout ---
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.error_label)
        layout.addWidget(self.confirm_button, alignment=Qt.AlignCenter)

        # --- Signals ---
        self.confirm_button.clicked.connect(self.verify_password)
        self.password_input.returnPressed.connect(self.verify_password)

    def verify_password(self):
        """
        Kiểm tra mật khẩu người dùng nhập vào.
        """
        entered_password = self.password_input.text()
        hashed_entered_password = hash_password(entered_password)

        if hashed_entered_password == self.correct_hashed_password:
            self.accept()  # Đóng dialog và trả về kết quả Accepted
        else:
            self.error_label.setText("Mật khẩu không chính xác!")
            self.password_input.selectAll()
