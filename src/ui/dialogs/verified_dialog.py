from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
# Thay đổi ở đây
from src.utils.helpers import Common

class VerifiedDialog(QDialog):
    def __init__(self, correct_hashed_password, parent=None):
        super().__init__(parent)
        self.correct_hashed_password = correct_hashed_password
        
        self.setWindowTitle("Xác thực quyền truy cập")
        self.setModal(True)
        self.setMinimumWidth(300)

        self.label = QLabel("Vui lòng nhập mật khẩu quản trị để tiếp tục:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.confirm_button = QPushButton("Xác nhận")
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.error_label)
        layout.addWidget(self.confirm_button, alignment=Qt.AlignCenter)

        self.confirm_button.clicked.connect(self.verify_password)
        self.password_input.returnPressed.connect(self.verify_password)

    def verify_password(self):
        entered_password = self.password_input.text()
        # Thay đổi ở đây
        hashed_entered_password = Common.hash_password(entered_password)

        if hashed_entered_password == self.correct_hashed_password:
            self.accept()
        else:
            self.error_label.setText("Mật khẩu không chính xác!")
            self.password_input.selectAll()