from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QCheckBox)
from PyQt6.QtCore import Qt
from src.core.splitter import PDFSplitter

class SplitWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input_file = ""
        self.page_count = 0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        file_layout.addWidget(self.file_label)
        
        select_button = QPushButton("选择PDF文件")
        select_button.clicked.connect(self.select_file)
        file_layout.addWidget(select_button)
        layout.addLayout(file_layout)
        
        # 页面范围输入区域
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("页面范围:"))
        
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("例如: 2-3;5-7 或 1,3;4,6-8")
        page_layout.addWidget(self.page_input)
        layout.addLayout(page_layout)
        
        # 提示标签
        self.hint_label = QLabel("支持的格式：用分号分隔不同文件的页面范围，每个范围支持：单页(1)，连续页(3-5)，组合(1,3-5,7)")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)
        
        # 选项区域
        options_layout = QHBoxLayout()
        self.separate_files_cb = QCheckBox("将每个页面保存为单独的文件")
        options_layout.addWidget(self.separate_files_cb)
        layout.addLayout(options_layout)
        
        # 提取按钮
        extract_button = QPushButton("提取页面")
        extract_button.clicked.connect(self.extract_pages)
        layout.addWidget(extract_button)
        
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if file_path:
            self.input_file = file_path
            success, result = PDFSplitter.get_pdf_page_count(file_path)
            if success:
                self.page_count = result
                self.file_label.setText(f"已选择: {file_path} (共{result}页)")
            else:
                self.file_label.setText("未选择文件")
                QMessageBox.critical(self, "错误", result)
                
    def parse_page_range(self, range_str):
        """解析页面范围字符串，返回页面组列表"""
        try:
            # 分割不同的页面组
            groups = range_str.split(';')
            page_groups = []
            
            for group in groups:
                pages = set()
                # 处理每个组内的页面范围
                parts = group.strip().split(',')
                for part in parts:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.update(range(start, end + 1))
                    else:
                        pages.add(int(part))
                if pages:  # 只添加非空的页面组
                    page_groups.append(sorted(list(pages)))
                    
            return page_groups if page_groups else None
            
        except:
            return None
            
    def extract_pages(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        range_str = self.page_input.text().strip()
        if not range_str:
            QMessageBox.warning(self, "警告", "请输入要提取的页面范围")
            return
            
        page_groups = self.parse_page_range(range_str)
        if not page_groups:
            QMessageBox.warning(self, "警告", "页面范围格式无效")
            return
            
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            ""
        )
        
        if output_dir:
            success, message = PDFSplitter.split_pdf(
                self.input_file,
                output_dir,
                page_groups,
                self.separate_files_cb.isChecked()
            )
            if success:
                QMessageBox.information(self, "成功", message)
                self.page_input.clear()
            else:
                QMessageBox.critical(self, "错误", message) 