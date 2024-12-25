from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, 
                             QListWidget, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from src.core.merger import PDFMerger

class MergeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建文件列表
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        # 添加文件按钮
        add_button = QPushButton("添加PDF文件")
        add_button.clicked.connect(self.add_files)
        layout.addWidget(add_button)
        
        # 移除选中文件按钮
        remove_button = QPushButton("移除选中文件")
        remove_button.clicked.connect(self.remove_selected)
        layout.addWidget(remove_button)
        
        # 合并按钮
        merge_button = QPushButton("合并PDF")
        merge_button.clicked.connect(self.merge_pdfs)
        layout.addWidget(merge_button)
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if files:
            self.pdf_files.extend(files)
            self.file_list.clear()
            self.file_list.addItems(self.pdf_files)
            
    def remove_selected(self):
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            self.pdf_files.remove(item.text())
        self.file_list.clear()
        self.file_list.addItems(self.pdf_files)
        
    def merge_pdfs(self):
        if len(self.pdf_files) < 2:
            QMessageBox.warning(self, "警告", "请至少添加两个PDF文件")
            return
            
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存合并后的PDF",
            "",
            "PDF文件 (*.pdf)"
        )
        
        if output_path:
            success, message = PDFMerger.merge_pdfs(self.pdf_files, output_path)
            if success:
                QMessageBox.information(self, "成功", message)
                self.pdf_files.clear()
                self.file_list.clear()
            else:
                QMessageBox.critical(self, "错误", message) 