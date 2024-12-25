from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QComboBox, QSpinBox, QListWidget, QProgressBar,
                             QDoubleSpinBox, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.editor import PDFEditor
import os

class BatchProcessThread(QThread):
    """批量处理线程"""
    progress = pyqtSignal(int)  # 进度信号
    finished = pyqtSignal(bool, str)  # 完成信号，返回(是否成功, 消息)
    
    def __init__(self, task_type, files, params):
        super().__init__()
        self.task_type = task_type
        self.files = files
        self.params = params
        
    def run(self):
        try:
            total = len(self.files)
            success_count = 0
            failed_files = []
            
            for i, file_path in enumerate(self.files):
                try:
                    # 构建输出文件路径
                    output_path = os.path.join(
                        self.params['output_dir'],
                        f"{os.path.splitext(os.path.basename(file_path))[0]}_{self.task_type}.pdf"
                    )
                    
                    if self.task_type == 'watermark':
                        success, message = PDFEditor.add_watermark(
                            file_path,
                            output_path,
                            self.params['text'],
                            self.params['opacity'],
                            self.params['angle']
                        )
                    elif self.task_type == 'remove_watermark':
                        success, message = PDFEditor.remove_watermark(
                            file_path,
                            output_path
                        )
                    elif self.task_type == 'compress':
                        success, message = PDFEditor.compress_pdf(
                            file_path,
                            output_path,
                            self.params['quality']
                        )
                    
                    if success:
                        success_count += 1
                    else:
                        failed_files.append(f"{os.path.basename(file_path)}: {message}")
                        
                except Exception as e:
                    failed_files.append(f"{os.path.basename(file_path)}: {str(e)}")
                    
                # 更新进度
                self.progress.emit(int((i + 1) / total * 100))
            
            # 生成详细的结果消息
            result_message = f"批量处理完成\n成功: {success_count}\n失败: {total - success_count}"
            if failed_files:
                result_message += "\n\n失败文件详情:\n" + "\n".join(failed_files)
            
            # 发送完成信号
            self.finished.emit(True, result_message)
            
        except Exception as e:
            self.finished.emit(False, f"批量处理失败: {str(e)}")

class BatchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.files = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件列表区域
        files_group = QGroupBox("待处理文件")
        files_layout = QVBoxLayout()
        
        # 文件列表
        self.file_list = QListWidget()
        files_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        file_buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("添加文件")
        add_button.clicked.connect(self.add_files)
        file_buttons_layout.addWidget(add_button)
        
        add_folder_button = QPushButton("添加文件夹")
        add_folder_button.clicked.connect(self.add_folder)
        file_buttons_layout.addWidget(add_folder_button)
        
        remove_button = QPushButton("移除选中")
        remove_button.clicked.connect(self.remove_selected)
        file_buttons_layout.addWidget(remove_button)
        
        clear_button = QPushButton("清空列表")
        clear_button.clicked.connect(self.clear_files)
        file_buttons_layout.addWidget(clear_button)
        
        files_layout.addLayout(file_buttons_layout)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)
        
        # 批量水印设置
        watermark_group = QGroupBox("批量水印")
        watermark_layout = QVBoxLayout()
        
        # 水印文本
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("水印文字:"))
        self.watermark_text = QLineEdit()
        text_layout.addWidget(self.watermark_text)
        watermark_layout.addLayout(text_layout)
        
        # 水印设置
        settings_layout = QHBoxLayout()
        
        # 透明度
        settings_layout.addWidget(QLabel("透明度:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.1, 1.0)
        self.opacity_spin.setValue(0.3)
        self.opacity_spin.setSingleStep(0.1)
        settings_layout.addWidget(self.opacity_spin)
        
        # 角度
        settings_layout.addWidget(QLabel("角度:"))
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(0, 360)
        self.angle_spin.setValue(45)
        self.angle_spin.setSingleStep(15)
        settings_layout.addWidget(self.angle_spin)
        
        watermark_layout.addLayout(settings_layout)
        
        # 水印操作按钮
        watermark_buttons_layout = QHBoxLayout()
        
        # 添加水印按钮
        add_watermark_button = QPushButton("批量添加水印")
        add_watermark_button.clicked.connect(lambda: self.start_batch_process('watermark'))
        watermark_buttons_layout.addWidget(add_watermark_button)
        
        # 移除水印按钮
        remove_watermark_button = QPushButton("批量移除水印")
        remove_watermark_button.clicked.connect(lambda: self.start_batch_process('remove_watermark'))
        watermark_buttons_layout.addWidget(remove_watermark_button)
        
        watermark_layout.addLayout(watermark_buttons_layout)
        watermark_group.setLayout(watermark_layout)
        layout.addWidget(watermark_group)
        
        # 批量压缩设置
        compress_group = QGroupBox("批量压缩")
        compress_layout = QVBoxLayout()
        
        # 压缩质量选择
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("压缩质量:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["高", "中", "低"])
        quality_layout.addWidget(self.quality_combo)
        compress_layout.addLayout(quality_layout)
        
        # 压缩按钮
        compress_button = QPushButton("批量压缩")
        compress_button.clicked.connect(lambda: self.start_batch_process('compress'))
        compress_layout.addWidget(compress_button)
        
        compress_group.setLayout(compress_layout)
        layout.addWidget(compress_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def add_files(self):
        """添加文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if files:
            self.files.extend(files)
            self.update_file_list()
            
    def add_folder(self):
        """添加文件夹中的所有PDF文件"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹"
        )
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        self.files.append(os.path.join(root, file))
            self.update_file_list()
            
    def remove_selected(self):
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        for item in selected_items:
            self.files.remove(item.text())
        self.update_file_list()
        
    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.update_file_list()
        
    def update_file_list(self):
        """更新文件列表显示"""
        self.file_list.clear()
        self.file_list.addItems(self.files)
        
    def start_batch_process(self, task_type):
        """开始批量处理"""
        if not self.files:
            QMessageBox.warning(self, "警告", "请先添加PDF文件")
            return
            
        # 获取输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录"
        )
        if not output_dir:
            return
            
        # 准备参数
        params = {'output_dir': output_dir}
        
        if task_type == 'watermark':
            # 检查水印文本
            watermark_text = self.watermark_text.text().strip()
            if not watermark_text:
                QMessageBox.warning(self, "警告", "请输入水印文字")
                return
                
            params.update({
                'text': watermark_text,
                'opacity': self.opacity_spin.value(),
                'angle': self.angle_spin.value()
            })
        elif task_type == 'compress':
            # 设置压缩质量
            quality_map = {"高": "high", "中": "medium", "低": "low"}
            params['quality'] = quality_map[self.quality_combo.currentText()]
            
        # 创建并启动处理线程
        self.process_thread = BatchProcessThread(task_type, self.files.copy(), params)
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(self.process_finished)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 禁用界面
        self.setEnabled(False)
        
        # 启动线程
        self.process_thread.start()
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def process_finished(self, success, message):
        """处理完成回调"""
        # 启用界面
        self.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 显示结果
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message) 