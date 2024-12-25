from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QComboBox, QSpinBox, QTabWidget, QListWidget,
                             QListWidgetItem, QDialog, QSlider, QToolButton,
                             QMenu)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QImage, QTransform, QDragEnterEvent, QDropEvent
from PIL import Image, ImageEnhance
from src.core.converter import PDFConverter
import os

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.edited_image = Image.open(image_path)
        self.rotation = 0
        self.brightness = 1.0
        self.contrast = 1.0
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("图片预处理")
        layout = QVBoxLayout(self)
        
        # 预览区域
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)
        
        # 旋转控制
        rotate_layout = QHBoxLayout()
        rotate_left = QPushButton("向左旋转")
        rotate_left.clicked.connect(lambda: self.rotate(-90))
        rotate_right = QPushButton("向右旋转")
        rotate_right.clicked.connect(lambda: self.rotate(90))
        rotate_layout.addWidget(rotate_left)
        rotate_layout.addWidget(rotate_right)
        layout.addLayout(rotate_layout)
        
        # 亮度控制
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("亮度:"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(50, 150)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.update_brightness)
        brightness_layout.addWidget(self.brightness_slider)
        layout.addLayout(brightness_layout)
        
        # 对比度控制
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("对比度:"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 150)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        contrast_layout.addWidget(self.contrast_slider)
        layout.addLayout(contrast_layout)
        
        # 确定和取消按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 显示初始预览
        self.update_preview()
        
    def rotate(self, angle):
        self.rotation = (self.rotation + angle) % 360
        self.update_preview()
        
    def update_brightness(self):
        self.brightness = self.brightness_slider.value() / 100
        self.update_preview()
        
    def update_contrast(self):
        self.contrast = self.contrast_slider.value() / 100
        self.update_preview()
        
    def update_preview(self):
        # 应用所有编辑
        img = self.edited_image.copy()
        
        # 旋转
        if self.rotation != 0:
            img = img.rotate(self.rotation, expand=True)
            
        # 亮度
        if self.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.brightness)
            
        # 对比度
        if self.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast)
            
        # 转换为QPixmap并显示
        img_qt = img.convert('RGB')
        data = img_qt.tobytes('raw', 'RGB')
        qimg = QImage(data, img_qt.size[0], img_qt.size[1], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # 缩放以适应预览区域
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
        
    def get_processed_image(self):
        """返回处理后的图片"""
        img = self.edited_image.copy()
        
        if self.rotation != 0:
            img = img.rotate(self.rotation, expand=True)
            
        if self.brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.brightness)
            
        if self.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.contrast)
            
        return img

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        
    def dropEvent(self, event: QDropEvent):
        super().dropEvent(event)
        # 通知父窗口更新图片列表
        if isinstance(self.parent(), ConvertWidget):
            self.parent().update_image_files_order()

class ConvertWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.input_file = ""
        self.image_files = []
        self.processed_images = {}  # 存储处理后的图片
        self.thumbnail_size = QSize(100, 100)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # PDF转图片选项卡
        pdf_to_image_widget = QWidget()
        pdf_to_image_layout = QVBoxLayout(pdf_to_image_widget)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        file_layout.addWidget(self.file_label)
        
        select_button = QPushButton("选择PDF文件")
        select_button.clicked.connect(self.select_pdf_file)
        file_layout.addWidget(select_button)
        pdf_to_image_layout.addLayout(file_layout)
        
        # 页面范围输入区域
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("页面范围:"))
        
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("例如: 1-3 (留空表示全部页面)")
        page_layout.addWidget(self.page_input)
        pdf_to_image_layout.addLayout(page_layout)
        
        # 转换选项区域
        options_layout = QVBoxLayout()
        
        # 图片格式选择
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG"])
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)
        
        # DPI设置
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("图片DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(200)
        self.dpi_spin.setSingleStep(50)
        dpi_layout.addWidget(self.dpi_spin)
        options_layout.addLayout(dpi_layout)
        
        pdf_to_image_layout.addLayout(options_layout)
        
        # 转换按钮
        convert_to_image_button = QPushButton("转换为图片")
        convert_to_image_button.clicked.connect(self.convert_to_images)
        pdf_to_image_layout.addWidget(convert_to_image_button)
        
        tab_widget.addTab(pdf_to_image_widget, "PDF转图片")
        
        # 图片转PDF选项卡
        image_to_pdf_widget = QWidget()
        image_to_pdf_layout = QVBoxLayout(image_to_pdf_widget)
        
        # 图片列表
        self.image_list = DraggableListWidget()
        self.image_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_list.setIconSize(self.thumbnail_size)
        self.image_list.setSpacing(10)
        self.image_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_context_menu)
        image_to_pdf_layout.addWidget(self.image_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        add_images_button = QPushButton("添加图片")
        add_images_button.clicked.connect(self.add_images)
        button_layout.addWidget(add_images_button)
        
        remove_image_button = QPushButton("移除选中")
        remove_image_button.clicked.connect(self.remove_selected_image)
        button_layout.addWidget(remove_image_button)
        
        clear_images_button = QPushButton("清空列表")
        clear_images_button.clicked.connect(self.clear_images)
        button_layout.addWidget(clear_images_button)
        
        # 添加排序按钮
        move_up_button = QPushButton("上移")
        move_up_button.clicked.connect(self.move_image_up)
        button_layout.addWidget(move_up_button)
        
        move_down_button = QPushButton("下移")
        move_down_button.clicked.connect(self.move_image_down)
        button_layout.addWidget(move_down_button)
        
        image_to_pdf_layout.addLayout(button_layout)
        
        # 页面大小选择
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("页面大小:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter"])
        size_layout.addWidget(self.page_size_combo)
        image_to_pdf_layout.addLayout(size_layout)
        
        # 转换按钮
        convert_to_pdf_button = QPushButton("转换为PDF")
        convert_to_pdf_button.clicked.connect(self.convert_to_pdf)
        image_to_pdf_layout.addWidget(convert_to_pdf_button)
        
        tab_widget.addTab(image_to_pdf_widget, "图片转PDF")
        
        layout.addWidget(tab_widget)
        
    def select_pdf_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        if file_path:
            self.input_file = file_path
            success, result = PDFConverter.get_pdf_page_count(file_path)
            if success:
                self.page_count = result
                self.file_label.setText(f"已选择: {file_path} (共{result}页)")
            else:
                self.file_label.setText("未选择文件")
                QMessageBox.critical(self, "错误", result)
                
    def parse_page_range(self, range_str):
        """解析页面范围字符串"""
        if not range_str.strip():
            return None, None
            
        try:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                if start < 1 or end < start:
                    return None, None
                return start, end
            else:
                page = int(range_str)
                if page < 1:
                    return None, None
                return page, page
        except:
            return None, None
            
    def convert_to_images(self):
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        # 解析页面范围
        first_page = None
        last_page = None
        range_str = self.page_input.text().strip()
        if range_str:
            first_page, last_page = self.parse_page_range(range_str)
            if first_page is None:
                QMessageBox.warning(self, "警告", "页面范围格式无效")
                return
            
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            ""
        )
        
        if output_dir:
            success, message = PDFConverter.pdf_to_images(
                self.input_file,
                output_dir,
                format=self.format_combo.currentText(),
                dpi=self.dpi_spin.value(),
                first_page=first_page,
                last_page=last_page
            )
            if success:
                QMessageBox.information(self, "成功", message)
                self.page_input.clear()
            else:
                QMessageBox.critical(self, "错误", message)
                
    def add_images(self):
        """添加图片到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        if files:
            self.image_files.extend(files)
            self.update_image_list()
            
    def remove_selected_image(self):
        """移除选中的图片"""
        current_row = self.image_list.currentRow()
        if current_row >= 0:
            del self.image_files[current_row]
            self.update_image_list()
            
    def clear_images(self):
        """清空图片列表"""
        self.image_files.clear()
        self.update_image_list()
        
    def update_image_list(self):
        """更新图片列表显示"""
        self.image_list.clear()
        for image_path in self.image_files:
            # 创建缩略图
            pixmap = self.create_thumbnail(image_path)
            
            # 创建列表项
            item = QListWidgetItem()
            item.setIcon(QIcon(pixmap))
            item.setText(os.path.basename(image_path))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(QSize(self.thumbnail_size.width(), 
                                 self.thumbnail_size.height() + 20))
            
            self.image_list.addItem(item)
            
    def move_image_up(self):
        """将选中的图片向上移动一位"""
        current_row = self.image_list.currentRow()
        if current_row > 0:
            # 交换当前项与上一项
            self.image_files[current_row], self.image_files[current_row - 1] = \
                self.image_files[current_row - 1], self.image_files[current_row]
            self.update_image_list()
            # 选中移动后的项
            self.image_list.setCurrentRow(current_row - 1)
            
    def move_image_down(self):
        """将选中的图片向下移动一位"""
        current_row = self.image_list.currentRow()
        if current_row >= 0 and current_row < len(self.image_files) - 1:
            # 交换当前项与下一项
            self.image_files[current_row], self.image_files[current_row + 1] = \
                self.image_files[current_row + 1], self.image_files[current_row]
            self.update_image_list()
            # 选中移动后的项
            self.image_list.setCurrentRow(current_row + 1)
        
    def show_context_menu(self, position: QPoint):
        """显示右键菜单"""
        item = self.image_list.itemAt(position)
        if item:
            menu = QMenu(self)
            edit_action = menu.addAction("编辑图片")
            edit_action.triggered.connect(lambda: self.edit_image(item))
            menu.exec(self.image_list.mapToGlobal(position))
            
    def edit_image(self, item: QListWidgetItem):
        """编辑选中的图片"""
        index = self.image_list.row(item)
        image_path = self.image_files[index]
        
        dialog = ImagePreviewDialog(image_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 保存处理后的图片
            processed_img = dialog.get_processed_image()
            self.processed_images[image_path] = processed_img
            
            # 更新缩略图
            pixmap = self.create_thumbnail(processed_img)
            item.setIcon(QIcon(pixmap))
            
    def create_thumbnail(self, image):
        """从PIL Image创建缩略图"""
        if isinstance(image, str):
            # 如果是文件路径，先检查是否有处理过的图片
            if image in self.processed_images:
                pil_image = self.processed_images[image]
            else:
                pil_image = Image.open(image)
        else:
            pil_image = image
            
        # 转换为QPixmap
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        data = pil_image.tobytes('raw', 'RGB')
        qimg = QImage(data, pil_image.size[0], pil_image.size[1], QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # 缩放
        return pixmap.scaled(
            self.thumbnail_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
    def update_image_files_order(self):
        """根据列表顺序更新图片文件列表"""
        new_order = []
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            filename = item.text()
            # 找到对应的完整路径
            for path in self.image_files:
                if os.path.basename(path) == filename:
                    new_order.append(path)
                    break
        self.image_files = new_order
        
    def convert_to_pdf(self):
        """将图片转换为PDF"""
        if not self.image_files:
            QMessageBox.warning(self, "警告", "请先添加图片")
            return
            
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存PDF文件",
            "",
            "PDF文件 (*.pdf)"
        )
        
        if output_path:
            # 准备处理后的图片列表
            images_to_convert = []
            for image_path in self.image_files:
                if image_path in self.processed_images:
                    images_to_convert.append(self.processed_images[image_path])
                else:
                    images_to_convert.append(image_path)
                    
            success, message = PDFConverter.images_to_pdf(
                images_to_convert,
                output_path,
                page_size=self.page_size_combo.currentText()
            )
            if success:
                QMessageBox.information(self, "成功", message)
                self.clear_images()
            else:
                QMessageBox.critical(self, "错误", message) 