from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QFileDialog, QMessageBox, QTabWidget,
                               QProgressBar, QSpacerItem, QSizePolicy, QLineEdit,
                               QDoubleSpinBox, QSpinBox, QGroupBox, QFormLayout, QComboBox, QDialog, QStackedWidget, QMenu, QCheckBox, QScrollArea, QApplication)
from PyQt6.QtCore import Qt, QSize, QMimeData, QPoint
from PyQt6.QtGui import QIcon, QAction, QDrag, QPixmap, QImage
import os
import sys
import io
from PIL import Image
from PyQt6.QtGui import QPixmap, QImage

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.core.editor import PDFEditor
from src.core.metadata import PDFMetadata

class ThumbnailListWidget(QWidget):
    """缩略图列表控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.thumbnails = []
        
    def handle_page_reorder(self, source_page, target_page):
        """处理页面重新排序"""
        # 获取源按钮和目标按钮
        source_btn = None
        target_btn = None
        for btn in self.thumbnails:
            if btn.page_num == source_page:
                source_btn = btn
            elif btn.page_num == target_page:
                target_btn = btn
        
        if source_btn and target_btn:
            # 获取按钮在布局中的位置
            source_index = self.layout.indexOf(source_btn)
            target_index = self.layout.indexOf(target_btn)
            
            # 移除源按钮
            self.layout.removeWidget(source_btn)
            
            # 在目标位置插入源按钮
            self.layout.insertWidget(target_index, source_btn)
            
            # 更新页码顺序
            self.update_page_numbers()
    
    def update_page_numbers(self):
        """更新页码顺序"""
        # 获取当前布局中的所有按钮
        buttons = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, DraggableThumbnailButton):
                buttons.append(widget)
        
        # 更新显示的页码，但保留原始页码
        for i, btn in enumerate(buttons):
            btn.page_num = i + 1
            btn.setToolTip(f"第 {i + 1} 页 (原始页码: {btn.original_page_num})")

class DraggableThumbnailButton(QPushButton):
    """可拖动的缩略图按钮"""
    def __init__(self, pixmap, page_num, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.original_page_num = page_num  # 保存原始页码
        self.setFixedSize(120, 160)
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(100, 140))
        self.setToolTip(f"第 {page_num} 页")
        self.original_pixmap = pixmap
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
            QPushButton:pressed {
                border-color: #0078d7;
                background-color: #e5f1fb;
            }
        """)
        
        self.setAcceptDrops(True)
        self.drag_start_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position:
            return
        
        # 计算移动距离
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # 创建拖放对象
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.page_num))
        drag.setMimeData(mime_data)
        
        # 设置拖放时的预览图像
        pixmap = self.original_pixmap.scaled(60, 80, Qt.AspectRatioMode.KeepAspectRatio)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(30, 40))
        
        # 执行拖放操作
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QPushButton {
                    border: 2px solid #0078d7;
                    border-radius: 5px;
                    padding: 5px;
                    background-color: #e5f1fb;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
            QPushButton:pressed {
                border-color: #0078d7;
                background-color: #e5f1fb;
            }
        """)

    def dropEvent(self, event):
        source_page = int(event.mimeData().text())
        target_page = self.page_num
        if source_page != target_page:
            # 获取父容器（ThumbnailListWidget）并调用其handle_page_reorder方法
            list_widget = self.parent()
            if isinstance(list_widget, ThumbnailListWidget):
                list_widget.handle_page_reorder(source_page, target_page)
        event.acceptProposedAction()
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
            QPushButton:pressed {
                border-color: #0078d7;
                background-color: #e5f1fb;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        """初始化用户界面"""
        # 设置窗口基本属性
        self.setWindowTitle('PDF工具箱')
        self.setMinimumSize(800, 600)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单布局
        menu_layout = QHBoxLayout()
        
        # 创建主要功能按钮
        watermark_btn = QPushButton('水印处理')
        compress_btn = QPushButton('PDF压缩')
        convert_btn = QPushButton('格式转换')
        page_btn = QPushButton('页面管理')
        security_btn = QPushButton('安全管理')
        
        # 设置按钮大小策略
        for btn in [watermark_btn, compress_btn, convert_btn, page_btn, security_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            menu_layout.addWidget(btn)
        
        # 连接按钮信号
        watermark_btn.clicked.connect(lambda: self.show_function_widget(self.create_watermark_tab()))
        compress_btn.clicked.connect(lambda: self.show_function_widget(self.create_compress_tab()))
        convert_btn.clicked.connect(lambda: self.show_function_widget(self.create_convert_tab()))
        page_btn.clicked.connect(self.show_page_management_menu)
        security_btn.clicked.connect(self.show_security_menu)
        
        # 添加菜单布局到主布局
        main_layout.addLayout(menu_layout)
        
        # 创建堆叠部件用于显示不同功能的界面
        self.stack_widget = QStackedWidget()
        main_layout.addWidget(self.stack_widget)
        
        # 默认显示水印处理界面
        self.show_function_widget(self.create_watermark_tab())
        
        # 创建状态栏
        self.statusBar().showMessage('就绪')
        
    def show_function_widget(self, widget):
        """显示功能界面"""
        # 清除当前显示的widget
        while self.stack_widget.count() > 0:
            current_widget = self.stack_widget.widget(0)
            self.stack_widget.removeWidget(current_widget)
            current_widget.deleteLater()
        
        # 添加新的widget
        self.stack_widget.addWidget(widget)
        self.stack_widget.setCurrentWidget(widget)
    
    def show_page_management_menu(self):
        """显示页面管理菜单"""
        menu = QMenu(self)
        
        # 添加分割PDF选项
        split_action = menu.addAction('分割PDF')
        split_action.triggered.connect(lambda: self.show_function_widget(self.create_split_tab()))
        
        # 添加合并PDF选项
        merge_action = menu.addAction('合并PDF')
        merge_action.triggered.connect(lambda: self.show_function_widget(self.create_merge_tab()))
        
        # 添加"重排序页面"菜单项
        reorder_action = menu.addAction('重排序页面')
        reorder_action.setStatusTip('重新排列PDF文件的页面顺序')
        reorder_action.triggered.connect(lambda: self.show_function_widget(self.create_reorder_tab()))
        
        # 获取触发按钮
        button = self.sender()
        
        # 在按钮下方显示菜单
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>PDF工具箱</h2>
        <p>版本：1.0.0</p>
        <p>一个功能强大的PDF处理工具，包括：</p>
        <ul>
            <li>水印处理（添加/移除）</li>
            <li>PDF压缩</li>
            <li>格式转换</li>
            <li>页面管理（分割/合并/重排序）</li>
        </ul>
        <p>作者：OpenAI</p>
        <p>Copyright © 2024 All rights reserved.</p>
        """
        
        QMessageBox.about(self, '关于', about_text)
    
    def create_watermark_tab(self):
        """创建水印处理标签页"""
        # 创建主容器和布局
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_file_layout = QHBoxLayout()
        self.watermark_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(lambda: self.select_file(self.watermark_input_path))
        input_file_layout.addWidget(self.watermark_input_path)
        input_file_layout.addWidget(select_input_btn)
        file_layout.addRow("输入文件：", input_file_layout)
        
        # 输出文件
        output_file_layout = QHBoxLayout()
        self.watermark_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.watermark_output_path))
        output_file_layout.addWidget(self.watermark_output_path)
        output_file_layout.addWidget(select_output_btn)
        file_layout.addRow("输出文件：", output_file_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 水印添加设置区域
        add_group = QGroupBox("添加水印")
        add_layout = QFormLayout()
        
        # 水印文字
        text_layout = QHBoxLayout()
        self.watermark_text = QLineEdit()
        self.watermark_text.setPlaceholderText("请输入水印文字")
        text_layout.addWidget(self.watermark_text)
        add_layout.addRow("水印文字：", text_layout)
        
        # 透明度
        opacity_layout = QHBoxLayout()
        self.watermark_opacity = QDoubleSpinBox()
        self.watermark_opacity.setRange(0.1, 1.0)
        self.watermark_opacity.setValue(0.3)
        self.watermark_opacity.setSingleStep(0.1)
        opacity_layout.addWidget(self.watermark_opacity)
        opacity_layout.addStretch()
        add_layout.addRow("透明度：", opacity_layout)
        
        # 旋转角度
        angle_layout = QHBoxLayout()
        self.watermark_angle = QSpinBox()
        self.watermark_angle.setRange(-180, 180)
        self.watermark_angle.setValue(45)
        self.watermark_angle.setSingleStep(15)
        angle_layout.addWidget(self.watermark_angle)
        angle_layout.addStretch()
        add_layout.addRow("旋转角度：", angle_layout)
        
        # 添加水印按钮
        add_btn = QPushButton('添加水印')
        add_btn.clicked.connect(self.add_watermark)
        add_layout.addRow("", add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # 水印移除设置区域
        remove_group = QGroupBox("移除水印")
        remove_layout = QFormLayout()
        
        # 移除模式
        mode_layout = QHBoxLayout()
        self.remove_mode = QComboBox()
        self.remove_mode.addItems(['标准模式', '增强模式'])
        self.remove_mode.currentIndexChanged.connect(self.on_remove_mode_changed)
        mode_layout.addWidget(self.remove_mode)
        mode_layout.addStretch()
        remove_layout.addRow("移除模式：", mode_layout)
        
        # 增强模式设置
        self.enhanced_settings = QWidget()
        enhanced_layout = QFormLayout(self.enhanced_settings)
        
        # 处理透明对象
        self.process_transparent = QCheckBox("处理透明对象")
        self.process_transparent.setChecked(True)
        enhanced_layout.addRow(self.process_transparent)
        
        # 处理图层
        self.process_layers = QCheckBox("处理图层")
        self.process_layers.setChecked(True)
        enhanced_layout.addRow(self.process_layers)
        
        # 处理注释
        self.process_annotations = QCheckBox("处理注释")
        self.process_annotations.setChecked(True)
        enhanced_layout.addRow(self.process_annotations)
        
        # 处理元数据
        self.process_metadata = QCheckBox("处理元数据")
        self.process_metadata.setChecked(True)
        enhanced_layout.addRow(self.process_metadata)
        
        # 初始隐藏增强设置
        self.enhanced_settings.hide()
        remove_layout.addRow(self.enhanced_settings)
        
        # 移除水印按钮
        remove_btn = QPushButton('移除水印')
        remove_btn.clicked.connect(self.remove_watermark)
        remove_layout.addRow("", remove_btn)
        
        remove_group.setLayout(remove_layout)
        layout.addWidget(remove_group)
        
        # 添加进度条
        self.watermark_progress = QProgressBar()
        self.watermark_progress.setVisible(False)
        layout.addWidget(self.watermark_progress)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        return tab
        
    def on_remove_mode_changed(self, index):
        """当水印移除模式改变时"""
        self.enhanced_settings.setVisible(index == 1)  # 1 表示增强模式
        
    def add_watermark(self):
        """���加水印"""
        # 检查输入
        if self.watermark_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件')
            return
        
        if self.watermark_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        if not self.watermark_text.text().strip():
            QMessageBox.warning(self, '警告', '请输入水印文字！')
            return
        
        try:
            # 显示进度条
            self.watermark_progress.setVisible(True)
            self.watermark_progress.setValue(0)
            self.statusBar().showMessage('正在添加水印...')
            
            # 添加水印
            success, message = PDFEditor.add_watermark(
                self.watermark_input_path.text(),
                self.watermark_output_path.text(),
                self.watermark_text.text(),
                self.watermark_opacity.value(),
                self.watermark_angle.value()
            )
            
            # 更新进度条
            self.watermark_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('添加水印成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('添加水印失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.watermark_progress.setVisible(False)
    
    def remove_watermark(self):
        """移除水印"""
        # 检查输入
        if self.watermark_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.watermark_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        try:
            # 显示进度条
            self.watermark_progress.setVisible(True)
            self.watermark_progress.setValue(0)
            self.statusBar().showMessage('正在移除水印...')
            
            # 根据模式选择移除方法
            if self.remove_mode.currentIndex() == 0:  # 标准模式
                success, message = PDFEditor.remove_watermark(
                    self.watermark_input_path.text(),
                    self.watermark_output_path.text()
                )
            else:  # 增强模式
                settings = {
                    'process_transparent': self.process_transparent.isChecked(),
                    'process_layers': self.process_layers.isChecked(),
                    'process_annotations': self.process_annotations.isChecked(),
                    'process_metadata': self.process_metadata.isChecked()
                }
                success, message = PDFEditor.remove_watermark_enhanced(
                    self.watermark_input_path.text(),
                    self.watermark_output_path.text(),
                    settings
                )
            
            # 更新进度条
            self.watermark_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('移除水印成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('移除水印失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.watermark_progress.setVisible(False)
    
    def compress_pdf(self):
        """压缩PDF"""
        # 检查输入
        if self.compress_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.compress_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        try:
            # 显示进度条
            self.compress_progress.setVisible(True)
            self.compress_progress.setValue(0)
            self.statusBar().showMessage('正在压缩...')
            
            # 获取压缩质量设置
            quality_map = {1: 'low', 2: 'medium', 3: 'high'}
            quality = quality_map[self.compress_quality.value()]
            
            # 压缩PDF
            success, message = PDFEditor.compress_pdf(
                self.compress_input_path.text(),
                self.compress_output_path.text(),
                quality=quality,
                image_dpi=self.compress_dpi.value()
            )
            
            # 更新进度条
            self.compress_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('压缩成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('压缩失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.compress_progress.setVisible(False)
    
    def select_directory(self, label):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            ""
        )
        if directory:
            label.setText(directory)
    
    def select_files(self, label):
        """选择多个文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*.*)"
        )
        if files:
            # 如果文件太多，只显示前几个
            if len(files) > 3:
                display_text = f"{'; '.join(files[:3])}... (共{len(files)}个文件)"
            else:
                display_text = "; ".join(files)
            label.setText(display_text)
            # 储完整的文件列表
            self.selected_image_files = files
    
    def convert_pdf_to_images(self):
        """将PDF转换为图片"""
        # 检查输入
        if self.convert_pdf_input.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.convert_image_output.text() == '未选择目录':
            QMessageBox.warning(self, '警告', '请选择输出目录！')
            return
        
        try:
            # 显示进度条
            self.convert_progress.setVisible(True)
            self.convert_progress.setValue(0)
            self.statusBar().showMessage('正在转换...')
            
            # 获取转换参数
            input_path = self.convert_pdf_input.text()
            output_dir = self.convert_image_output.text()
            image_format = self.image_format.currentText().lower()
            dpi = self.convert_dpi.value()
            
            # 调用转换方法
            success, message = PDFEditor.pdf_to_images(
                input_path,
                output_dir,
                image_format,
                dpi
            )
            
            # 更新进度条
            self.convert_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('转换成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('转换失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.convert_progress.setVisible(False)
    
    def convert_images_to_pdf(self):
        """将图片转换为PDF"""
        # 检查输入
        if not hasattr(self, 'selected_image_files') or not self.selected_image_files:
            QMessageBox.warning(self, '警告', '请先选择输入图片文件！')
            return
        
        if self.convert_pdf_output.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出PDF文件位置！')
            return
        
        try:
            # 显示进度条
            self.convert_progress.setVisible(True)
            self.convert_progress.setValue(0)
            self.statusBar().showMessage('正在转换...')
            
            # 获取转换参数
            input_paths = self.selected_image_files
            output_path = self.convert_pdf_output.text()
            page_size = self.page_size.currentText()
            margin = self.page_margin.value()
            
            # 调用转换方法
            success, message = PDFEditor.images_to_pdf(
                input_paths,
                output_path,
                page_size,
                margin
            )
            
            # 更新进度条
            self.convert_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('转换成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('转换失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.convert_progress.setVisible(False)
    
    def on_split_mode_changed(self, index):
        """分割模式改变时的处理"""
        # 隐藏所有参数控件
        self.split_params_widget.hide()
        self.pages_per_file_widget.hide()
        self.selective_split_widget.hide()
        
        # 根据选择的模式显示相关控件
        if index == 1:  # 指定页数
            self.pages_per_file_widget.show()
        elif index == 2:  # 自定义范围
            self.split_params_widget.show()
        elif index == 3:  # 选择性分组
            self.selective_split_widget.show()
    
    def select_files_for_merge(self, label):
        """选择多个PDF文件用于合并"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if files:
            # 如果文件太多，只显示前几个
            if len(files) > 3:
                display_text = f"{'; '.join(files[:3])}... (共{len(files)}个文件)"
            else:
                display_text = "; ".join(files)
            label.setText(display_text)
            # 存储完整的文件列表
            self.selected_pdf_files = files
    
    def split_pdf(self):
        """分割PDF文件"""
        # 检查输入
        if self.split_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.split_output_dir.text() == '未选择目录':
            QMessageBox.warning(self, '警告', '请选择输出目录！')
            return
        
        try:
            # 显示进度条
            self.split_progress.setVisible(True)
            self.split_progress.setValue(0)
            self.statusBar().showMessage('正在分割...')
            
            # 获取分割参数
            input_path = self.split_input_path.text()
            output_dir = self.split_output_dir.text()
            mode = self.split_mode.currentIndex()
            
            if mode == 0:  # 单页拆分
                page_groups = None  # 使用默认的单页分割
            elif mode == 1:  # 指定页数
                pages_per_file = self.pages_per_file.value()
                page_groups = []
                total_pages = PDFEditor.get_pdf_page_count(input_path)
                for i in range(0, total_pages, pages_per_file):
                    end = min(i + pages_per_file, total_pages)
                    page_groups.append(f"{i+1}-{end}")
            elif mode == 2:  # 自定义范围
                page_groups = self.split_params.text().strip().split(',')
            else:  # 选择性分组
                # 检查是否有至少一个文件组
                if not self.file_groups:
                    QMessageBox.warning(self, '警告', '请至少添加一个文件组！')
                    return
                
                # 检查每个文件是否都有输入
                for group in self.file_groups:
                    if not group['pages_input'].text().strip():
                        QMessageBox.warning(self, '警告', '请为每个文件组输入页面范围！')
                        return
                
                # 获取总页数
                total_pages = PDFEditor.get_pdf_page_count(input_path)
                
                # 收集所有指定页面
                all_selected_pages = set()
                page_groups = []
                
                # 处理每个文件组
                for group in self.file_groups:
                    pages = self.parse_page_ranges(group['pages_input'].text().strip())
                    # 检查页码是否有效
                    if any(p < 1 or p > total_pages for p in pages):
                        QMessageBox.warning(self, '警告', f'页码超出范围 (1-{total_pages})！')
                        return
                    # 检查是否有重复页码
                    if any(p in all_selected_pages for p in pages):
                        QMessageBox.warning(self, '警告', '存在重复的页码！')
                        return
                    
                    all_selected_pages.update(pages)
                    if self.sort_pages.isChecked():
                        # 按输入顺序
                        page_groups.append(','.join(map(str, pages)))
                    else:
                        # 按原始顺序
                        page_groups.append(','.join(map(str, sorted(pages))))
                
                # 处理剩余页面
                if self.save_remainder.isChecked():
                    remaining_pages = sorted(list(set(range(1, total_pages + 1)) - all_selected_pages))
                    if remaining_pages:
                        page_groups.append(','.join(map(str, remaining_pages)))
            
            # 调用分割方法
            success, message = PDFEditor.split_pdf(
                input_path,
                output_dir,
                page_groups
            )
            
            # 更新进度条
            self.split_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('分割成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('分割失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.split_progress.setVisible(False)
    
    def parse_page_ranges(self, page_ranges_str):
        """解析页面范围字符串，返回页码列表"""
        pages = []
        ranges = page_ranges_str.split(',')
        for r in ranges:
            r = r.strip()
            if '-' in r:
                start, end = map(int, r.split('-'))
                pages.extend(range(start, end + 1))
            else:
                pages.append(int(r))
        return pages
    
    def merge_pdfs(self):
        """合并PDF文件"""
        # 检查输入
        if not hasattr(self, 'selected_pdf_files') or not self.selected_pdf_files:
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.merge_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        try:
            # 显示进度条
            self.merge_progress.setVisible(True)
            self.merge_progress.setValue(0)
            self.statusBar().showMessage('正在合并...')
            
            # 调用合并方法
            success, message = PDFEditor.merge_pdfs(
                self.selected_pdf_files,
                self.merge_output_path.text()
            )
            
            # 更新进度条
            self.merge_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('合并成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('合并失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.merge_progress.setVisible(False)
    
    def on_reorder_file_selected(self):
        """当选择了要重排序的PDF文件时"""
        # 先调用原来的文件选择方法
        self.select_file(self.reorder_input_path)
        
        # 如果选择了文件，则加载缩略图
        if self.reorder_input_path.text() != '未选择文件':
            self.load_reorder_thumbnails(self.reorder_input_path.text())
    
    def load_reorder_thumbnails(self, pdf_path):
        """加载用于重排序的PDF缩略图"""
        try:
            # 清除现有缩略图
            for button in self.reorder_thumbnails.thumbnails:
                button.deleteLater()
            self.reorder_thumbnails.thumbnails.clear()
            
            # 使用pdf2image生成缩略图
            from pdf2image import convert_from_path
            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=72,
                    size=(120, 160),
                    poppler_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'poppler', 'bin'),
                    userpw=None
                )
            except Exception as e:
                if "Command Line Error: Incorrect password" in str(e):
                    QMessageBox.warning(self, '警告', 'PDF文件受密码保护，无法显示预览')
                    return
                else:
                    raise e
            
            # 创建缩略图按钮
            for i, image in enumerate(images):
                # 将PIL图像转换为QPixmap
                img_byte_array = io.BytesIO()
                image.save(img_byte_array, format='PNG', quality=85, optimize=True)
                qimg = QImage.fromData(img_byte_array.getvalue())
                pixmap = QPixmap.fromImage(qimg)
                
                # 创建可拖动的缩略图按钮
                thumb_btn = DraggableThumbnailButton(pixmap, i+1, self.reorder_thumbnails)
                self.reorder_thumbnails.layout.addWidget(thumb_btn)
                self.reorder_thumbnails.thumbnails.append(thumb_btn)
            
            # 添加弹性空间
            self.reorder_thumbnails.layout.addStretch()
            
        except Exception as e:
            QMessageBox.warning(self, '警告', f'加载缩略图失败：{str(e)}')
    
    def handle_page_reorder(self, source_page, target_page):
        """处理页面重新排序"""
        # 获取源按钮和目标按钮
        source_btn = None
        target_btn = None
        for btn in self.reorder_thumbnails.thumbnails:
            if btn.page_num == source_page:
                source_btn = btn
            elif btn.page_num == target_page:
                target_btn = btn
        
        if source_btn and target_btn:
            # 获取按钮在布局中的位置
            source_index = self.reorder_thumbnails.layout.indexOf(source_btn)
            target_index = self.reorder_thumbnails.layout.indexOf(target_btn)
            
            # 移除源按钮
            self.reorder_thumbnails.layout.removeWidget(source_btn)
            
            # 在目标位置插入源按钮
            self.reorder_thumbnails.layout.insertWidget(target_index, source_btn)
            
            # 更新页码顺序
            self.update_page_numbers()
    
    def update_page_numbers(self):
        """更新页码顺序"""
        # 获取当前布局中的所有按钮
        buttons = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, DraggableThumbnailButton):
                buttons.append(widget)
        
        # 只更新显示的页码，不更改原始页码
        for i, btn in enumerate(buttons):
            btn.page_num = i + 1
            btn.setToolTip(f"第 {i + 1} 页 (原始页码: {btn.original_page_num})")
    
    def apply_page_reorder(self):
        """应用页面重排序"""
        if self.reorder_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.reorder_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输出PDF文件！')
            return
        
        try:
            # 显示进度条
            self.reorder_progress.setVisible(True)
            self.reorder_progress.setValue(0)
            self.statusBar().showMessage('正在重排序...')
            
            # 获取新的页面顺序
            page_order = []
            for i in range(self.reorder_thumbnails.layout.count()):
                widget = self.reorder_thumbnails.layout.itemAt(i).widget()
                if isinstance(widget, DraggableThumbnailButton):
                    # 使用original_page_num而不是page_num
                    page_order.append(str(widget.original_page_num))
            
            if not page_order:
                raise Exception("无法获取页面顺序")
            
            # 调用重排序方法
            success, message = PDFEditor.reorder_pages(
                self.reorder_input_path.text(),
                self.reorder_output_path.text(),
                ','.join(page_order)
            )
            
            # 更新进度条
            self.reorder_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('重排序成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('重排序失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.reorder_progress.setVisible(False)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜��
        file_menu = menubar.addMenu('文件')
        
        # 添加"打开文件"菜单项
        open_action = QAction('打开', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('打开PDF文件')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 添加分隔
        file_menu.addSeparator()
        
        # 添加"退出"菜单项
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('退出应用')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 页面管理菜单
        page_menu = menubar.addMenu('页面管理')
        
        # 添加"分割PDF"菜单项
        split_action = QAction('分割PDF', self)
        split_action.setStatusTip('将PDF文件分割成多个文件')
        split_action.triggered.connect(lambda: self.show_function_widget(self.create_split_tab()))
        page_menu.addAction(split_action)
        
        # 添加"合并PDF"菜单项
        merge_action = QAction('合并PDF', self)
        merge_action.setStatusTip('将多个PDF文件合并为一个')
        merge_action.triggered.connect(lambda: self.show_function_widget(self.create_merge_tab()))
        page_menu.addAction(merge_action)
        
        # 添加"重排序页面"菜单项
        reorder_action = QAction('重排序页面', self)
        reorder_action.setStatusTip('重新排列PDF文件的页面顺序')
        reorder_action.triggered.connect(lambda: self.show_function_widget(self.create_reorder_tab()))
        page_menu.addAction(reorder_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 添加"关于"菜单项
        about_action = QAction('关于', self)
        about_action.setStatusTip('关于本软件')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_file_group(self, parent_layout):
        """添加一个文件组"""
        # 创建文件组容器
        group_widget = QWidget()
        group_layout = QHBoxLayout(group_widget)
        
        # 页面范围输入
        pages_input = QLineEdit()
        pages_input.setPlaceholderText("例如：1-3,5,8-9")
        group_layout.addWidget(pages_input)
        
        # 删除按钮
        if self.file_groups:  # 只有不是第一个组才显示删除按钮
            delete_btn = QPushButton('删除')
            delete_btn.clicked.connect(lambda: self.delete_file_group(group_widget, parent_layout))
            group_layout.addWidget(delete_btn)
        
        # 将组件添加到布局中
        # 找到"添加文件组"按钮的位置
        insert_index = parent_layout.count() - 2  # 减2是因为要跳过按钮布局和剩余页面设置
        parent_layout.insertWidget(insert_index, group_widget)
        
        # 保存文件组信息
        self.file_groups.append({
            'widget': group_widget,
            'pages_input': pages_input
        })
        
    def delete_file_group(self, group_widget, parent_layout):
        """删除一个文件组"""
        # 从列表中移除
        self.file_groups = [g for g in self.file_groups if g['widget'] != group_widget]
        # 从布局中移除
        parent_layout.removeWidget(group_widget)
        group_widget.deleteLater() 
    
    def on_split_file_selected(self):
        """当选择了要分割的PDF文件时"""
        # 先调用原来的文件选择方法
        self.select_file(self.split_input_path)
        
        # 如果选择了文件，则加载缩略图
        if self.split_input_path.text() != '未选择文件':
            self.load_pdf_thumbnails(self.split_input_path.text())
    
    def load_pdf_thumbnails(self, pdf_path):
        """加载PDF文件的缩略图"""
        try:
            # 清除现有缩略图
            for i in reversed(range(self.thumbnails_layout.count())): 
                widget = self.thumbnails_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            # 使用pdf2image生成缩略图
            from pdf2image import convert_from_path
            try:
                # 使用较低的DPI生成缩略图以加快加载速度
                images = convert_from_path(
                    pdf_path,
                    dpi=72,  # 使用较低的DPI加快加载速度
                    size=(120, 160),  # 直接指定缩略图大小
                    poppler_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'poppler', 'bin'),
                    userpw=None  # 尝试空密码
                )
            except Exception as e:
                if "Command Line Error: Incorrect password" in str(e):
                    # 如果是密码错误，提示用户
                    QMessageBox.warning(self, '警告', 'PDF文件���密码保护，无法显示预览')
                    return
                else:
                    raise e
            
            # 创建缩略图按钮
            self.thumbnail_buttons = []  # 储所有缩略图按钮引用
            for i, image in enumerate(images):
                # 将PIL图像转换为QPixmap
                img_byte_array = io.BytesIO()
                image.save(img_byte_array, format='PNG', quality=85, optimize=True)
                qimg = QImage.fromData(img_byte_array.getvalue())
                pixmap = QPixmap.fromImage(qimg)
                
                # 创建缩略图按钮
                thumb_btn = QPushButton()
                thumb_btn.setFixedSize(120, 160)
                thumb_btn.setIcon(QIcon(pixmap))
                thumb_btn.setIconSize(QSize(100, 140))
                thumb_btn.setToolTip(f"第 {i+1} 页")
                thumb_btn.setCheckable(True)
                
                # 设置样式
                thumb_btn.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #ccc;
                        border-radius: 5px;
                        padding: 5px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        border-color: #999;
                    }
                """)
                
                # 连接点击信号
                thumb_btn.clicked.connect(lambda checked, page=i+1: self.on_thumbnail_clicked(page))
                
                # 添加到布局
                self.thumbnails_layout.addWidget(thumb_btn)
                self.thumbnail_buttons.append(thumb_btn)
            
            # 添加弹性空间
            self.thumbnails_layout.addStretch()
            
        except Exception as e:
            QMessageBox.warning(self, '警告', f'加载缩略图失败：{str(e)}')
    
    def on_thumbnail_clicked(self, page):
        """当缩略图被点击时"""
        mode = self.split_mode.currentIndex()
        
        if mode == 3:  # 选择性分组模式
            # 获取当前选中的文件组
            current_group = None
            for group in self.file_groups:
                if group['widget'].hasFocus():
                    current_group = group
                    break
            
            # 如果没有找到焦点所在的文件组，使用第一个组
            if not current_group and self.file_groups:
                current_group = self.file_groups[0]
            
            if current_group:
                # 获取当前输入框的内
                current_text = current_group['pages_input'].text().strip()
                
                # 添页码
                if current_text:
                    current_pages = self.parse_page_ranges(current_text)
                    if page in current_pages:
                        # 如果页面已经在列表中，则移除它
                        current_pages.remove(page)
                        self.thumbnail_buttons[page-1].setChecked(False)
                    else:
                        # 否则添加页面
                        current_pages.append(page)
                        self.thumbnail_buttons[page-1].setChecked(True)
                    # 将面列表转换回文本格式
                    new_text = self.format_page_ranges(sorted(current_pages))
                else:
                    new_text = str(page)
                    self.thumbnail_buttons[page-1].setChecked(True)
                
                # 更新输入框
                current_group['pages_input'].setText(new_text)
        else:  # 其他模式
            # 更新应的输入框
            if mode == 2:  # 自定义范围
                current_text = self.split_params.text().strip()
                if current_text:
                    current_pages = self.parse_page_ranges(current_text)
                    if page in current_pages:
                        current_pages.remove(page)
                        self.thumbnail_buttons[page-1].setChecked(False)
                    else:
                        current_pages.append(page)
                        self.thumbnail_buttons[page-1].setChecked(True)
                    new_text = self.format_page_ranges(sorted(current_pages))
                else:
                    new_text = str(page)
                    self.thumbnail_buttons[page-1].setChecked(True)
                self.split_params.setText(new_text)
            elif mode == 1:  # 指定页数
                # 在指定页数模式下，点击缩略图不执行任何操作
                pass
            elif mode == 0:  # 单页拆分
                # 在单页拆分模式下，点击缩略图不执行任何操作
                pass 
    
    def format_page_ranges(self, pages):
        """将页码列表转换为范围表示
        例如：[1,2,3,5,6,8] -> "1-3,5-6,8"
        """
        if not pages:
            return ""
            
        ranges = []
        start = pages[0]
        prev = start
        
        for page in pages[1:] + [None]:
            if page != prev + 1:
                if start == prev:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{prev}")
                start = page
            prev = page
            
        return ','.join(ranges) 

    def create_compress_tab(self):
        """创建PDF压缩标签页"""
        # 创建主容器和布局
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_file_layout = QHBoxLayout()
        self.compress_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(lambda: self.select_file(self.compress_input_path))
        input_file_layout.addWidget(self.compress_input_path)
        input_file_layout.addWidget(select_input_btn)
        file_layout.addRow("输入文件：", input_file_layout)
        
        # 输出文件
        output_file_layout = QHBoxLayout()
        self.compress_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.compress_output_path))
        output_file_layout.addWidget(self.compress_output_path)
        output_file_layout.addWidget(select_output_btn)
        file_layout.addRow("输出文件：", output_file_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 压缩设置区域
        compress_group = QGroupBox("压缩设置")
        compress_layout = QFormLayout()
        
        # 压缩质量
        quality_layout = QHBoxLayout()
        self.compress_quality = QSpinBox()
        self.compress_quality.setRange(1, 3)
        self.compress_quality.setValue(2)
        quality_label = QLabel("(1=小文件优先 2=平衡 3=质量优先)")
        quality_layout.addWidget(self.compress_quality)
        quality_layout.addWidget(quality_label)
        quality_layout.addStretch()
        compress_layout.addRow("压缩等级：", quality_layout)
        
        # 图片DPI设置
        dpi_layout = QHBoxLayout()
        self.compress_dpi = QSpinBox()
        self.compress_dpi.setRange(72, 300)
        self.compress_dpi.setValue(150)
        self.compress_dpi.setSingleStep(72)
        dpi_label = QLabel("DPI (72=标准 150=常用 300=高清)")
        dpi_layout.addWidget(self.compress_dpi)
        dpi_layout.addWidget(dpi_label)
        dpi_layout.addStretch()
        compress_layout.addRow("图片分辨率：", dpi_layout)
        
        # 文本压缩选项
        text_compress_layout = QHBoxLayout()
        self.text_compress = QCheckBox("压缩文本")
        self.text_compress.setChecked(True)
        text_compress_layout.addWidget(self.text_compress)
        text_compress_layout.addStretch()
        compress_layout.addRow("文本压缩：", text_compress_layout)
        
        # 图片压缩选项
        image_compress_layout = QHBoxLayout()
        self.image_compress = QCheckBox("压缩图片")
        self.image_compress.setChecked(True)
        image_compress_layout.addWidget(self.image_compress)
        image_compress_layout.addStretch()
        compress_layout.addRow("图片压缩：", image_compress_layout)
        
        # 删除元数据选项
        metadata_layout = QHBoxLayout()
        self.remove_metadata = QCheckBox("删除元数据")
        self.remove_metadata.setChecked(True)
        metadata_layout.addWidget(self.remove_metadata)
        metadata_layout.addStretch()
        compress_layout.addRow("元数据处理：", metadata_layout)
        
        compress_group.setLayout(compress_layout)
        layout.addWidget(compress_group)
        
        # 压缩按钮
        button_layout = QHBoxLayout()
        compress_btn = QPushButton('开始压缩')
        compress_btn.clicked.connect(self.compress_pdf)
        button_layout.addWidget(compress_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.compress_progress = QProgressBar()
        self.compress_progress.setVisible(False)
        layout.addWidget(self.compress_progress)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        return tab 

    def create_convert_tab(self):
        """创建格式转换标签页"""
        # 创建主容器和布局
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # PDF转图片域
        pdf_to_image_group = QGroupBox("PDF转图片")
        pdf_to_image_layout = QFormLayout()
        
        # 输入PDF文件
        input_pdf_layout = QHBoxLayout()
        self.convert_pdf_input = QLabel('未选择文件')
        select_pdf_btn = QPushButton('浏览...')
        select_pdf_btn.clicked.connect(lambda: self.select_file(self.convert_pdf_input))
        input_pdf_layout.addWidget(self.convert_pdf_input)
        input_pdf_layout.addWidget(select_pdf_btn)
        pdf_to_image_layout.addRow("输入PDF：", input_pdf_layout)
        
        # 输出目录
        output_dir_layout = QHBoxLayout()
        self.convert_image_output = QLabel('未选择目录')
        select_dir_btn = QPushButton('浏览...')
        select_dir_btn.clicked.connect(lambda: self.select_directory(self.convert_image_output))
        output_dir_layout.addWidget(self.convert_image_output)
        output_dir_layout.addWidget(select_dir_btn)
        pdf_to_image_layout.addRow("输出目录：", output_dir_layout)
        
        # 图片格式选择
        format_layout = QHBoxLayout()
        self.image_format = QComboBox()
        self.image_format.addItems(['PNG', 'JPEG', 'TIFF'])
        format_layout.addWidget(self.image_format)
        format_layout.addStretch()
        pdf_to_image_layout.addRow("图片格式：", format_layout)
        
        # DPI设置
        dpi_layout = QHBoxLayout()
        self.convert_dpi = QSpinBox()
        self.convert_dpi.setRange(72, 600)
        self.convert_dpi.setValue(300)
        self.convert_dpi.setSingleStep(72)
        dpi_label = QLabel("DPI (72=标准 300=高清 600=超清)")
        dpi_layout.addWidget(self.convert_dpi)
        dpi_layout.addWidget(dpi_label)
        dpi_layout.addStretch()
        pdf_to_image_layout.addRow("分辨率：", dpi_layout)
        
        # 转换按钮
        pdf_to_image_btn = QPushButton('开始转换')
        pdf_to_image_btn.clicked.connect(self.convert_pdf_to_images)
        pdf_to_image_layout.addRow("", pdf_to_image_btn)
        
        pdf_to_image_group.setLayout(pdf_to_image_layout)
        layout.addWidget(pdf_to_image_group)
        
        # 图片转PDF区域
        image_to_pdf_group = QGroupBox("图片转PDF")
        image_to_pdf_layout = QFormLayout()
        
        # 输入图片文件
        input_images_layout = QHBoxLayout()
        self.convert_images_input = QLabel('未选择文件')
        select_images_btn = QPushButton('浏览...')
        select_images_btn.clicked.connect(lambda: self.select_files(self.convert_images_input))
        input_images_layout.addWidget(self.convert_images_input)
        input_images_layout.addWidget(select_images_btn)
        image_to_pdf_layout.addRow("输入图片：", input_images_layout)
        
        # 输出PDF文件
        output_pdf_layout = QHBoxLayout()
        self.convert_pdf_output = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.convert_pdf_output))
        output_pdf_layout.addWidget(self.convert_pdf_output)
        output_pdf_layout.addWidget(select_output_btn)
        image_to_pdf_layout.addRow("输出PDF：", output_pdf_layout)
        
        # 页面大小选择
        page_size_layout = QHBoxLayout()
        self.page_size = QComboBox()
        self.page_size.addItems(['A4', 'Letter', '自动'])
        page_size_layout.addWidget(self.page_size)
        page_size_layout.addStretch()
        image_to_pdf_layout.addRow("页面大小：", page_size_layout)
        
        # 页边距设置
        margin_layout = QHBoxLayout()
        self.page_margin = QSpinBox()
        self.page_margin.setRange(0, 100)
        self.page_margin.setValue(10)
        self.page_margin.setSuffix(" mm")
        margin_layout.addWidget(self.page_margin)
        margin_layout.addStretch()
        image_to_pdf_layout.addRow("页边距：", margin_layout)
        
        # 转换按钮
        image_to_pdf_btn = QPushButton('开始转换')
        image_to_pdf_btn.clicked.connect(self.convert_images_to_pdf)
        image_to_pdf_layout.addRow("", image_to_pdf_btn)
        
        image_to_pdf_group.setLayout(image_to_pdf_layout)
        layout.addWidget(image_to_pdf_group)
        
        # 添加进度条
        self.convert_progress = QProgressBar()
        self.convert_progress.setVisible(False)
        layout.addWidget(self.convert_progress)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        return tab 

    def create_split_tab(self):
        """创建PDF分割标签页"""
        # 创建主容器和布局
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_split_layout = QHBoxLayout()
        self.split_input_path = QLabel('未选择文件')
        select_split_btn = QPushButton('浏览...')
        select_split_btn.clicked.connect(self.on_split_file_selected)
        input_split_layout.addWidget(self.split_input_path)
        input_split_layout.addWidget(select_split_btn)
        file_layout.addRow("输入PDF：", input_split_layout)
        
        # 输出目录
        output_split_layout = QHBoxLayout()
        self.split_output_dir = QLabel('未��择目录')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_directory(self.split_output_dir))
        output_split_layout.addWidget(self.split_output_dir)
        output_split_layout.addWidget(select_output_btn)
        file_layout.addRow("输出目录：", output_split_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 缩略图区域
        thumbnails_group = QGroupBox("页面预览")
        thumbnails_layout = QVBoxLayout()
        
        # 创建缩略图滚动区域
        thumbnails_scroll = QScrollArea()
        thumbnails_scroll.setWidgetResizable(True)
        thumbnails_scroll.setMinimumHeight(200)
        thumbnails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        thumbnails_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建缩略图容器
        self.thumbnails_widget = QWidget()
        self.thumbnails_layout = QHBoxLayout(self.thumbnails_widget)
        self.thumbnails_layout.setSpacing(10)
        self.thumbnails_layout.setContentsMargins(10, 10, 10, 10)
        thumbnails_scroll.setWidget(self.thumbnails_widget)
        thumbnails_layout.addWidget(thumbnails_scroll)
        
        thumbnails_group.setLayout(thumbnails_layout)
        layout.addWidget(thumbnails_group)
        
        # 分割设置区域
        split_group = QGroupBox("分割设置")
        split_layout = QFormLayout()
        
        # 分割方式
        split_mode_layout = QHBoxLayout()
        self.split_mode = QComboBox()
        self.split_mode.addItems(['单页拆分', '指定页数', '自定义范围', '选择性分组'])
        self.split_mode.currentIndexChanged.connect(self.on_split_mode_changed)
        split_mode_layout.addWidget(self.split_mode)
        split_mode_layout.addStretch()
        split_layout.addRow("分割方式：", split_mode_layout)
        
        # 分割参数（初始隐藏）
        self.split_params_widget = QWidget()
        split_params_layout = QHBoxLayout(self.split_params_widget)
        self.split_params = QLineEdit()
        self.split_params.setPlaceholderText("例如：1-3,4,5-7")
        split_params_layout.addWidget(self.split_params)
        split_layout.addRow("分割参数：", self.split_params_widget)
        self.split_params_widget.hide()
        
        # 每个文件的页数（初始隐藏）
        self.pages_per_file_widget = QWidget()
        pages_per_file_layout = QHBoxLayout(self.pages_per_file_widget)
        self.pages_per_file = QSpinBox()
        self.pages_per_file.setRange(1, 100)
        self.pages_per_file.setValue(1)
        pages_per_file_layout.addWidget(self.pages_per_file)
        pages_per_file_layout.addStretch()
        split_layout.addRow("每个文件页数：", self.pages_per_file_widget)
        self.pages_per_file_widget.hide()
        
        # 选择性分组设置（初始隐藏）
        self.selective_split_widget = QWidget()
        selective_split_layout = QVBoxLayout(self.selective_split_widget)
        
        # 文件组列表
        self.file_groups = []
        
        # 添加第一个文件组
        self.add_file_group(selective_split_layout)
        
        # 添加/删除文件组的按钮
        buttons_layout = QHBoxLayout()
        add_group_btn = QPushButton('添加文件组')
        add_group_btn.clicked.connect(lambda: self.add_file_group(selective_split_layout))
        buttons_layout.addWidget(add_group_btn)
        selective_split_layout.addLayout(buttons_layout)
        
        # 剩余页面设置
        remainder_group = QGroupBox("剩余页面设置")
        remainder_layout = QVBoxLayout()
        
        self.save_remainder = QCheckBox("保存剩余页面到新文件")
        self.save_remainder.setChecked(True)
        remainder_layout.addWidget(self.save_remainder)
        
        remainder_group.setLayout(remainder_layout)
        selective_split_layout.addWidget(remainder_group)
        
        # 页面排序选项
        self.sort_pages = QCheckBox("按输入顺序排列页")
        self.sort_pages.setChecked(True)
        selective_split_layout.addWidget(self.sort_pages)
        
        split_layout.addRow("", self.selective_split_widget)
        self.selective_split_widget.hide()
        
        split_group.setLayout(split_layout)
        layout.addWidget(split_group)
        
        # 分割按钮
        button_layout = QHBoxLayout()
        split_btn = QPushButton('开始分割')
        split_btn.clicked.connect(self.split_pdf)
        button_layout.addWidget(split_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.split_progress = QProgressBar()
        self.split_progress.setVisible(False)
        layout.addWidget(self.split_progress)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        return tab
        
    def on_split_mode_changed(self, index):
        """当分割模式改变时"""
        # 隐藏所有参数设置
        self.split_params_widget.hide()
        self.pages_per_file_widget.hide()
        self.selective_split_widget.hide()
        
        # 根据选择的模式显示相应的设置
        if index == 1:  # 指定页数
            self.pages_per_file_widget.show()
        elif index == 2:  # 自定义范围
            self.split_params_widget.show()
        elif index == 3:  # 选择性分组
            self.selective_split_widget.show()

    def create_merge_tab(self):
        """创建PDF合并标签页"""
        # 创建主容器和布局
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件列表
        input_merge_layout = QHBoxLayout()
        self.merge_input_list = QLabel('未选择文件')
        select_merge_btn = QPushButton('浏览...')
        select_merge_btn.clicked.connect(lambda: self.select_files_for_merge(self.merge_input_list))
        input_merge_layout.addWidget(self.merge_input_list)
        input_merge_layout.addWidget(select_merge_btn)
        file_layout.addRow("输入PDF：", input_merge_layout)
        
        # 输出文件
        output_merge_layout = QHBoxLayout()
        self.merge_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.merge_output_path))
        output_merge_layout.addWidget(self.merge_output_path)
        output_merge_layout.addWidget(select_output_btn)
        file_layout.addRow("输出PDF：", output_merge_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 合并设置区域
        merge_group = QGroupBox("合并设置")
        merge_layout = QFormLayout()
        
        # 页面大小选项
        page_size_layout = QHBoxLayout()
        self.merge_page_size = QComboBox()
        self.merge_page_size.addItems(['保持原始大小', '统一为最大', '统一为最小'])
        page_size_layout.addWidget(self.merge_page_size)
        page_size_layout.addStretch()
        merge_layout.addRow("页面大小：", page_size_layout)
        
        # 页面方向选项
        orientation_layout = QHBoxLayout()
        self.merge_orientation = QComboBox()
        self.merge_orientation.addItems(['保持原始方向', '统一为纵向', '统一为横向'])
        orientation_layout.addWidget(self.merge_orientation)
        orientation_layout.addStretch()
        merge_layout.addRow("页面方向：", orientation_layout)
        
        merge_group.setLayout(merge_layout)
        layout.addWidget(merge_group)
        
        # 合并按钮
        button_layout = QHBoxLayout()
        merge_btn = QPushButton('开始合并')
        merge_btn.clicked.connect(self.merge_pdfs)
        button_layout.addWidget(merge_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.merge_progress = QProgressBar()
        self.merge_progress.setVisible(False)
        layout.addWidget(self.merge_progress)
        
        # 设置滚动区域的内容
        scroll.setWidget(content_widget)
        
        return tab
        
    def select_files_for_merge(self, label):
        """选择要合并的PDF文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if files:
            # 如果文件太多，只显示前几个
            if len(files) > 3:
                display_text = f"{'; '.join(files[:3])}... (共{len(files)}个文件)"
            else:
                display_text = "; ".join(files)
            label.setText(display_text)
            # 存储完整的文件列表
            self.selected_pdf_files = files

    def create_reorder_tab(self):
        """创建页面重排序标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.reorder_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(self.on_reorder_file_selected)
        input_layout.addWidget(self.reorder_input_path)
        input_layout.addWidget(select_input_btn)
        file_layout.addRow("输入PDF：", input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.reorder_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.reorder_output_path))
        output_layout.addWidget(self.reorder_output_path)
        output_layout.addWidget(select_output_btn)
        file_layout.addRow("输出PDF：", output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 缩略图区域
        thumbnails_group = QGroupBox("页面排序")
        thumbnails_layout = QVBoxLayout()
        
        # 创建缩略图滚动区域
        thumbnails_scroll = QScrollArea()
        thumbnails_scroll.setWidgetResizable(True)
        thumbnails_scroll.setMinimumHeight(200)
        thumbnails_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        thumbnails_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建缩略图容器
        self.reorder_thumbnails = ThumbnailListWidget()
        thumbnails_scroll.setWidget(self.reorder_thumbnails)
        thumbnails_layout.addWidget(thumbnails_scroll)
        
        thumbnails_group.setLayout(thumbnails_layout)
        layout.addWidget(thumbnails_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        reorder_btn = QPushButton('应用重排序')
        reorder_btn.clicked.connect(self.apply_page_reorder)
        button_layout.addWidget(reorder_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.reorder_progress = QProgressBar()
        self.reorder_progress.setVisible(False)
        layout.addWidget(self.reorder_progress)
        
        return tab

    def select_file(self, label):
        """选择单个文件"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if file:
            label.setText(file)
            if hasattr(self, 'load_pdf_thumbnails') and label == getattr(self, 'split_input_path', None):
                self.load_pdf_thumbnails(file)
            elif hasattr(self, 'load_reorder_thumbnails') and label == getattr(self, 'reorder_input_path', None):
                self.load_reorder_thumbnails(file)

    def select_save_file(self, label):
        """选择保存文件的位置"""
        file, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存位置",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if file:
            # 确保文件扩展名为.pdf
            if not file.lower().endswith('.pdf'):
                file += '.pdf'
            label.setText(file)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self.drag_start_position:
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.page_num))
        drag.setMimeData(mime_data)
        
        # 创建拖动时的预览图像
        pixmap = self.original_pixmap.scaled(
            80, 100,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        
        drag.exec(Qt.DropAction.MoveAction)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QPushButton {
                    border: 2px solid #0078d7;
                    border-radius: 5px;
                    padding: 5px;
                    background-color: #e5f1fb;
                }
            """)
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
            QPushButton:pressed {
                border-color: #0078d7;
                background-color: #e5f1fb;
            }
        """)
        
    def dropEvent(self, event):
        source_page = int(event.mimeData().text())
        target_page = self.page_num
        if source_page != target_page:
            # 获取父容器（ThumbnailListWidget）并调用其handle_page_reorder方法
            list_widget = self.parent()
            if isinstance(list_widget, ThumbnailListWidget):
                list_widget.handle_page_reorder(source_page, target_page)
        event.acceptProposedAction()
        self.setStyleSheet("""
            QPushButton {
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QPushButton:hover {
                border-color: #999;
            }
            QPushButton:pressed {
                border-color: #0078d7;
                background-color: #e5f1fb;
            }
        """) 

    def show_security_menu(self):
        """显示安全管理菜单"""
        menu = QMenu(self)
        
        # 添加加密PDF选项
        encrypt_action = menu.addAction('加密PDF')
        encrypt_action.triggered.connect(lambda: self.show_function_widget(self.create_encrypt_tab()))
        
        # 添加解密PDF选项
        decrypt_action = menu.addAction('解密PDF')
        decrypt_action.triggered.connect(lambda: self.show_function_widget(self.create_decrypt_tab()))
        
        # 添加"添加页码"菜单项
        add_page_numbers_action = menu.addAction('添加页码')
        add_page_numbers_action.setStatusTip('在PDF页面添加页码')
        add_page_numbers_action.triggered.connect(lambda: self.show_function_widget(self.create_page_numbers_tab()))
        
        # 获取触发按钮
        button = self.sender()
        
        # 在按钮下方显示菜单
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def create_encrypt_tab(self):
        """创建PDF加密标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.encrypt_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(lambda: self.select_file(self.encrypt_input_path))
        input_layout.addWidget(self.encrypt_input_path)
        input_layout.addWidget(select_input_btn)
        file_layout.addRow("输入PDF：", input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.encrypt_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.encrypt_output_path))
        output_layout.addWidget(self.encrypt_output_path)
        output_layout.addWidget(select_output_btn)
        file_layout.addRow("输出PDF：", output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 密码设置区域
        password_group = QGroupBox("密码设置")
        password_layout = QFormLayout()
        
        # 用户密码（打开密码）
        self.user_password = QLineEdit()
        self.user_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addRow("打开密码：", self.user_password)
        
        # 所有者密码（权限密码）
        self.owner_password = QLineEdit()
        self.owner_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addRow("权限密码：", self.owner_password)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # 权限设置区域
        permissions_group = QGroupBox("权限设置")
        permissions_layout = QVBoxLayout()
        
        self.allow_print = QCheckBox("允许打印")
        self.allow_modify = QCheckBox("允许修改")
        self.allow_copy = QCheckBox("允许复制内容")
        self.allow_annotate = QCheckBox("允许添加注释")
        
        # 设置默认权限
        self.allow_print.setChecked(True)
        self.allow_copy.setChecked(True)
        
        permissions_layout.addWidget(self.allow_print)
        permissions_layout.addWidget(self.allow_modify)
        permissions_layout.addWidget(self.allow_copy)
        permissions_layout.addWidget(self.allow_annotate)
        
        permissions_group.setLayout(permissions_layout)
        layout.addWidget(permissions_group)
        
        # 加密按钮
        button_layout = QHBoxLayout()
        encrypt_btn = QPushButton('开始加密')
        encrypt_btn.clicked.connect(self.encrypt_pdf)
        button_layout.addWidget(encrypt_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.encrypt_progress = QProgressBar()
        self.encrypt_progress.setVisible(False)
        layout.addWidget(self.encrypt_progress)
        
        return tab
    
    def create_decrypt_tab(self):
        """创建PDF解密标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.decrypt_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(lambda: self.select_file(self.decrypt_input_path))
        input_layout.addWidget(self.decrypt_input_path)
        input_layout.addWidget(select_input_btn)
        file_layout.addRow("输入PDF：", input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.decrypt_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.decrypt_output_path))
        output_layout.addWidget(self.decrypt_output_path)
        output_layout.addWidget(select_output_btn)
        file_layout.addRow("输出PDF：", output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 密码输入区域
        password_group = QGroupBox("密码输入")
        password_layout = QFormLayout()
        
        self.decrypt_password = QLineEdit()
        self.decrypt_password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addRow("PDF密码：", self.decrypt_password)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # 密码破解选项
        crack_group = QGroupBox("密码破解")
        crack_layout = QVBoxLayout()
        
        self.try_crack = QCheckBox("尝试破解密码")
        crack_layout.addWidget(self.try_crack)
        
        crack_group.setLayout(crack_layout)
        layout.addWidget(crack_group)
        
        # 解密按钮
        button_layout = QHBoxLayout()
        decrypt_btn = QPushButton('开始解密')
        decrypt_btn.clicked.connect(self.decrypt_pdf)
        button_layout.addWidget(decrypt_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.decrypt_progress = QProgressBar()
        self.decrypt_progress.setVisible(False)
        layout.addWidget(self.decrypt_progress)
        
        return tab
    
    def create_page_numbers_tab(self):
        """创建添加页码标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.page_numbers_input_path = QLabel('未选择文件')
        select_input_btn = QPushButton('浏览...')
        select_input_btn.clicked.connect(lambda: self.select_file(self.page_numbers_input_path))
        input_layout.addWidget(self.page_numbers_input_path)
        input_layout.addWidget(select_input_btn)
        file_layout.addRow("输入PDF：", input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.page_numbers_output_path = QLabel('未选择文件')
        select_output_btn = QPushButton('浏览...')
        select_output_btn.clicked.connect(lambda: self.select_save_file(self.page_numbers_output_path))
        output_layout.addWidget(self.page_numbers_output_path)
        output_layout.addWidget(select_output_btn)
        file_layout.addRow("输出PDF：", output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 页码设置区域
        settings_group = QGroupBox("页码设置")
        settings_layout = QFormLayout()
        
        # 起始页码
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 9999)
        self.start_number.setValue(1)
        settings_layout.addRow("起始页码：", self.start_number)
        
        # 页码位置
        self.page_position = QComboBox()
        self.page_position.addItems(["底部", "顶部"])
        settings_layout.addRow("页码位置：", self.page_position)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 添加页码按钮
        button_layout = QHBoxLayout()
        add_numbers_btn = QPushButton('添加页码')
        add_numbers_btn.clicked.connect(self.add_page_numbers)
        button_layout.addWidget(add_numbers_btn)
        layout.addLayout(button_layout)
        
        # 添加进度条
        self.page_numbers_progress = QProgressBar()
        self.page_numbers_progress.setVisible(False)
        layout.addWidget(self.page_numbers_progress)
        
        return tab
    
    def encrypt_pdf(self):
        """加密PDF文件"""
        if self.encrypt_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.encrypt_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        if not self.user_password.text() and not self.owner_password.text():
            QMessageBox.warning(self, '警告', '请至少设置一个密码！')
            return
        
        try:
            # 显示进度条
            self.encrypt_progress.setVisible(True)
            self.encrypt_progress.setValue(0)
            self.statusBar().showMessage('正在加密...')
            
            # 获取权限设置
            permissions = {
                'print': self.allow_print.isChecked(),
                'modify': self.allow_modify.isChecked(),
                'copy': self.allow_copy.isChecked(),
                'annotate': self.allow_annotate.isChecked()
            }
            
            # 调用加密方法
            success, message = PDFMetadata.add_encryption(
                self.encrypt_input_path.text(),
                self.encrypt_output_path.text(),
                self.user_password.text(),
                self.owner_password.text(),
                permissions
            )
            
            # 更新进度条
            self.encrypt_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('加密成功')
                # 清空密码输入框
                self.user_password.clear()
                self.owner_password.clear()
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('加密失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.encrypt_progress.setVisible(False)
    
    def decrypt_pdf(self):
        """解密PDF文件"""
        if self.decrypt_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.decrypt_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        try:
            # 显示进度条
            self.decrypt_progress.setVisible(True)
            self.decrypt_progress.setValue(0)
            self.statusBar().showMessage('正在处理...')
            
            if self.try_crack.isChecked():
                # 尝试破解密码
                self.statusBar().showMessage('正在尝试破解密码...')
                success, result = PDFMetadata.crack_password(self.decrypt_input_path.text())
                if success:
                    self.decrypt_password.setText(result)
                    QMessageBox.information(self, '成功', f'密码破解成功：{result}')
                else:
                    QMessageBox.warning(self, '失败', result)
                    return
            
            # 提取PDF内容
            success, message = PDFMetadata.extract_content(
                self.decrypt_input_path.text(),
                self.decrypt_output_path.text()
            )
            
            # 更新进度条
            self.decrypt_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('解密成功')
                # 清空密码输入框
                self.decrypt_password.clear()
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('解密失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.decrypt_progress.setVisible(False)
    
    def add_page_numbers(self):
        """添加页码"""
        if self.page_numbers_input_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请先选择输入PDF文件！')
            return
        
        if self.page_numbers_output_path.text() == '未选择文件':
            QMessageBox.warning(self, '警告', '请选择输出文件位置！')
            return
        
        try:
            # 显示进度条
            self.page_numbers_progress.setVisible(True)
            self.page_numbers_progress.setValue(0)
            self.statusBar().showMessage('正在添加页码...')
            
            # 获取页码位置
            position = 'bottom' if self.page_position.currentText() == '底部' else 'top'
            
            # 调用添加页码方法
            success, message = PDFEditor.add_page_numbers(
                self.page_numbers_input_path.text(),
                self.page_numbers_output_path.text(),
                self.start_number.value(),
                position
            )
            
            # 更新进度条
            self.page_numbers_progress.setValue(100)
            
            # 显示结果
            if success:
                QMessageBox.information(self, '成功', message)
                self.statusBar().showMessage('页码添加成功')
            else:
                QMessageBox.warning(self, '失败', message)
                self.statusBar().showMessage('页码添加失败')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}')
            self.statusBar().showMessage('发生错误')
        
        finally:
            # 隐藏进度条
            self.page_numbers_progress.setVisible(False)