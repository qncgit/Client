# qncgit/client/Client-53f2080517b2db6a5fda56d26b9a57e2a1b36cf5/src/ui/dialogs/verified_dialog.py
from PyQt5.QtGui import QColor
from qfluentwidgets import SubtitleLabel, LineEdit, MessageBoxBase, CaptionLabel
from src.utils.helpers import Common

class VerifiedDialog(MessageBoxBase):
    """
    Hộp thoại xác thực quyền truy cập, sử dụng MessageBoxBase.
    """
    def __init__(self, correct_hashed_password, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Xác thực quyền truy cập", self)
        self.correct_hashed_password = correct_hashed_password
        
        self.password_input = LineEdit(self)
        self.password_input.setPlaceholderText("Nhập mật khẩu admin...")

        self.warningLabel = CaptionLabel("Mật khẩu không chính xác!", self)
        # Thiết lập màu cho cảnh báo (cho cả light/dark theme)
        self.warningLabel.setTextColor("#cf1010", QColor(255, 28, 32))
        # Ẩn cảnh báo lúc đầu
        self.warningLabel.hide()

        # Thêm các widget vào layout của dialog
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.password_input)
        self.viewLayout.addWidget(self.warningLabel)
        
        # Cấu hình các nút bấm
        self.yesButton.setText("Xác nhận")
        self.cancelButton.setText("Hủy")
        self.yesButton.clicked.connect(self.validate)
        self.password_input.returnPressed.connect(self.validate)

    def validate(self):
        entered_password = self.password_input.text()
        hashed_entered_password = Common.hash_password(entered_password)

        if hashed_entered_password == self.correct_hashed_password:
            self.warningLabel.hide()
            super().accept()
        else:
            self.warningLabel.show()
            self.password_input.selectAll()
            self.password_input.setFocus()