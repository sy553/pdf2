import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.ui.main_window import MainWindow
from src.utils.setup_poppler import download_poppler

def check_dependencies():
    """检查并配置依赖项"""
    # 检查poppler
    poppler_dir = os.path.join(os.path.dirname(__file__), 'poppler', 'bin')
    if not os.path.exists(poppler_dir):
        # 下载并配置poppler
        if not download_poppler():
            QMessageBox.critical(None, "错误", "无法配置poppler，PDF转图片功能可能无法使用")
            return False
    return True

def main():
    app = QApplication(sys.argv)
    
    # 检查依赖项
    check_dependencies()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 