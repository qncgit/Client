import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """
    Hàm chính để khởi tạo và chạy ứng dụng.
    """
    app = QApplication(sys.argv)
    # Thêm một số style để giao diện trông hiện đại hơn
    app.setStyle('Fusion')
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()