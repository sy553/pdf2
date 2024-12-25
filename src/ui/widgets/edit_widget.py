import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QComboBox, QSpinBox, QTabWidget, QDoubleSpinBox)
from PyQt6.QtCore import Qt
from src.core.editor import PDFEditor

class EditWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input_file = ""
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
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 水印选项卡
        watermark_widget = QWidget()
        watermark_layout = QVBoxLayout(watermark_widget)
        
        # 水印文本输入
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("水印文字:"))
        self.watermark_text = QLineEdit()
        text_layout.addWidget(self.watermark_text)
        watermark_layout.addLayout(text_layout)
        
        # 水印透明度
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("透明度:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setValue(0.3)
        self.opacity_spin.setSingleStep(0.1)
        opacity_layout.addWidget(self.opacity_spin)
        watermark_layout.addLayout(opacity_layout)
        
        # 水印角度
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("旋转角度:"))
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(0, 360)
        self.angle_spin.setValue(45)
        self.angle_spin.setSingleStep(15)
        angle_layout.addWidget(self.angle_spin)
        watermark_layout.addLayout(angle_layout)
        
        # 添加水印按钮
        add_watermark_button = QPushButton("添加水印")
        add_watermark_button.clicked.connect(self.add_watermark)
        watermark_layout.addWidget(add_watermark_button)
        
        tab_widget.addTab(watermark_widget, "添加水印")
        
        # 旋转页面选项卡
        rotate_widget = QWidget()
        rotate_layout = QVBoxLayout(rotate_widget)
        
        # 旋转角度选择
        rotation_layout = QHBoxLayout()
        rotation_layout.addWidget(QLabel("旋转角度:"))
        self.rotation_combo = QComboBox()
        self.rotation_combo.addItems(["90度", "180度", "270度"])
        rotation_layout.addWidget(self.rotation_combo)
        rotate_layout.addLayout(rotation_layout)
        
        # 页面范围输入
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("页面范围:"))
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("例如: 1,3-5,7 (留空表示全部页面)")
        page_layout.addWidget(self.page_input)
        rotate_layout.addLayout(page_layout)
        
        # 旋转按钮
        rotate_button = QPushButton("旋转页面")
        rotate_button.clicked.connect(self.rotate_pages)
        rotate_layout.addWidget(rotate_button)
        
        tab_widget.addTab(rotate_widget, "旋转页面")
        
        # 页码选项卡
        number_widget = QWidget()
        number_layout = QVBoxLayout(number_widget)
        
        # 起始页码
        start_num_layout = QHBoxLayout()
        start_num_layout.addWidget(QLabel("起始页码:"))
        self.start_num_spin = QSpinBox()
        self.start_num_spin.setRange(1, 9999)
        self.start_num_spin.setValue(1)
        start_num_layout.addWidget(self.start_num_spin)
        number_layout.addLayout(start_num_layout)
        
        # 页码位置
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("页码位置:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["底部", "顶部"])
        position_layout.addWidget(self.position_combo)
        number_layout.addLayout(position_layout)
        
        # 添加页码按钮
        add_numbers_button = QPushButton("添加页码")
        add_numbers_button.clicked.connect(self.add_page_numbers)
        number_layout.addWidget(add_numbers_button)
        
        tab_widget.addTab(number_widget, "添加页码")
        
        # 压缩选项卡
        compress_widget = QWidget()
        compress_layout = QVBoxLayout(compress_widget)
        
        # 压缩质量选择
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("压缩质量:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高", "中", "低"])
        quality_layout.addWidget(self.quality_combo)
        compress_layout.addLayout(quality_layout)
        
        # 压缩按钮
        compress_button = QPushButton("压缩PDF")
        compress_button.clicked.connect(self.compress_pdf)
        compress_layout.addWidget(compress_button)
        
        tab_widget.addTab(compress_widget, "压缩PDF")
        
        layout.addWidget(tab_widget)
        
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if file_path:
            self.input_file = file_path
            self.file_label.setText(f"已选择: {file_path}")
            
    def get_output_path(self, suffix):
        """获取输出文件路径"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return None
            
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            f"{os.path.splitext(self.input_file)[0]}_{suffix}.pdf",
            "PDF文件 (*.pdf)"
        )
        return output_path
            
    def add_watermark(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        watermark_text = self.watermark_text.text().strip()
        if not watermark_text:
            QMessageBox.warning(self, "警告", "请输入水印文字")
            return
            
        output_path = self.get_output_path("水印")
        if output_path:
            success, message = PDFEditor.add_watermark(
                self.input_file,
                output_path,
                watermark_text,
                self.opacity_spin.value(),
                self.angle_spin.value()
            )
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "错误", message)
                
    def parse_page_range(self, range_str):
        """解析页面范围字符串"""
        if not range_str.strip():
            return None
            
        pages = set()
        try:
            parts = range_str.split(',')
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start, end + 1))
                else:
                    pages.add(int(part))
            return sorted(list(pages))
        except:
            return None
                
    def rotate_pages(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        # 解析旋转角度
        rotation_text = self.rotation_combo.currentText()
        rotation = int(rotation_text.replace("度", ""))
        
        # 解析页面范围
        pages = None
        range_str = self.page_input.text().strip()
        if range_str:
            pages = self.parse_page_range(range_str)
            if pages is None:
                QMessageBox.warning(self, "警告", "页面范围格式无效")
                return
                
        output_path = self.get_output_path("旋转")
        if output_path:
            success, message = PDFEditor.rotate_pages(
                self.input_file,
                output_path,
                rotation,
                pages
            )
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "错误", message)
                
    def add_page_numbers(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        output_path = self.get_output_path("页码")
        if output_path:
            position = 'bottom' if self.position_combo.currentText() == "底部" else 'top'
            success, message = PDFEditor.add_page_numbers(
                self.input_file,
                output_path,
                self.start_num_spin.value(),
                position
            )
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "错误", message)
                
    def compress_pdf(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        # 解析压缩质量
        quality_map = {"高": "high", "中": "medium", "低": "low"}
        quality = quality_map[self.quality_combo.currentText()]
        
        output_path = self.get_output_path("压缩")
        if output_path:
            success, message = PDFEditor.compress_pdf(
                self.input_file,
                output_path,
                quality
            )
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "错误", message)