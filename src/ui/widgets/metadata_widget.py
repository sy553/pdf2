import os
import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QFileDialog, QMessageBox,
                             QTabWidget, QGridLayout, QCheckBox, QGroupBox,
                             QApplication)
from PyQt6.QtCore import Qt
from src.core.metadata import PDFMetadata

class MetadataWidget(QWidget):
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
        
        # 元数据选项卡
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout(metadata_widget)
        
        # 当前元数据示区域
        current_group = QGroupBox("当前元数据")
        current_layout = QVBoxLayout()
        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        current_layout.addWidget(self.metadata_label)
        current_group.setLayout(current_layout)
        metadata_layout.addWidget(current_group)
        
        # 元数据编辑区域
        edit_group = QGroupBox("编辑元数据")
        edit_layout = QGridLayout()
        
        # 标题
        edit_layout.addWidget(QLabel("标题:"), 0, 0)
        self.title_edit = QLineEdit()
        edit_layout.addWidget(self.title_edit, 0, 1)
        
        # 作者
        edit_layout.addWidget(QLabel("作者:"), 1, 0)
        self.author_edit = QLineEdit()
        edit_layout.addWidget(self.author_edit, 1, 1)
        
        # 主题
        edit_layout.addWidget(QLabel("主题:"), 2, 0)
        self.subject_edit = QLineEdit()
        edit_layout.addWidget(self.subject_edit, 2, 1)
        
        # 关键词
        edit_layout.addWidget(QLabel("关键词:"), 3, 0)
        self.keywords_edit = QLineEdit()
        edit_layout.addWidget(self.keywords_edit, 3, 1)
        
        edit_group.setLayout(edit_layout)
        metadata_layout.addWidget(edit_group)
        
        # 更新元数据按钮
        update_button = QPushButton("更新元数据")
        update_button.clicked.connect(self.update_metadata)
        metadata_layout.addWidget(update_button)
        
        tab_widget.addTab(metadata_widget, "元数据")
        
        # 加密选项卡
        encrypt_widget = QWidget()
        encrypt_layout = QVBoxLayout(encrypt_widget)
        
        # 密码设置区域
        password_group = QGroupBox("密码设置")
        password_layout = QGridLayout()
        
        # 用户密码（打开文档密码）
        password_layout.addWidget(QLabel("打开密码:"), 0, 0)
        self.user_password_edit = QLineEdit()
        self.user_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.user_password_edit, 0, 1)
        
        # 所有者密码（编辑文档密码）
        password_layout.addWidget(QLabel("权限密码:"), 1, 0)
        self.owner_password_edit = QLineEdit()
        self.owner_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.owner_password_edit, 1, 1)
        
        password_group.setLayout(password_layout)
        encrypt_layout.addWidget(password_group)
        
        # 权限设置区域
        permissions_group = QGroupBox("权限设置")
        permissions_layout = QVBoxLayout()
        
        self.print_cb = QCheckBox("允许打印")
        self.print_cb.setChecked(True)
        permissions_layout.addWidget(self.print_cb)
        
        self.modify_cb = QCheckBox("允许修改")
        permissions_layout.addWidget(self.modify_cb)
        
        self.copy_cb = QCheckBox("允许复制内容")
        self.copy_cb.setChecked(True)
        permissions_layout.addWidget(self.copy_cb)
        
        self.annotate_cb = QCheckBox("允许添加注释")
        permissions_layout.addWidget(self.annotate_cb)
        
        permissions_group.setLayout(permissions_layout)
        encrypt_layout.addWidget(permissions_group)
        
        # 加密按钮
        encrypt_button = QPushButton("加密PDF")
        encrypt_button.clicked.connect(self.encrypt_pdf)
        encrypt_layout.addWidget(encrypt_button)
        
        tab_widget.addTab(encrypt_widget, "加密")
        
        # 修改破解选项卡
        crack_widget = QWidget()
        crack_layout = QVBoxLayout(crack_widget)
        
        # 说明文本
        info_label = QLabel("此功能将尝试提取加密PDF的内容并创建新的PDF文件。\n注意：某些PDF可能无法提取内容。")
        info_label.setWordWrap(True)
        crack_layout.addWidget(info_label)
        
        # 破解按钮
        extract_button = QPushButton("提取内容")
        extract_button.clicked.connect(self.extract_content)
        crack_layout.addWidget(extract_button)
        
        tab_widget.addTab(crack_widget, "内容提取")
        
        layout.addWidget(tab_widget)
        
        # 初始化常用密码列表
        self.common_passwords = []
        self.dict_file_path = None
        
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
            self.load_metadata()
            
    def load_metadata(self):
        """加载并显示当前PDF的元数据"""
        success, result = PDFMetadata.get_metadata(self.input_file)
        if success:
            if isinstance(result, dict) and result.get('Encrypted'):
                # 如果是加密文件，显示基本信息
                metadata_text = "文件已加密\n"
                metadata_text += f"文件大小: {result.get('FileSize', '未知')}\n"
                self.metadata_label.setText(metadata_text)
                
                # 清空编辑���
                self.title_edit.clear()
                self.author_edit.clear()
                self.subject_edit.clear()
                self.keywords_edit.clear()
                
                # 禁用编辑框
                self.title_edit.setEnabled(False)
                self.author_edit.setEnabled(False)
                self.subject_edit.setEnabled(False)
                self.keywords_edit.setEnabled(False)
            else:
                # 显示当前元数据
                metadata_text = "文件大小: {}\n页数: {}\n".format(
                    result.get('FileSize', '未知'),
                    result.get('Pages', '未知')
                )
                for key, value in result.items():
                    if key not in ['FileSize', 'Pages']:
                        metadata_text += f"{key}: {value}\n"
                self.metadata_label.setText(metadata_text)
                
                # 填充编辑框
                self.title_edit.setText(result.get('Title', ''))
                self.author_edit.setText(result.get('Author', ''))
                self.subject_edit.setText(result.get('Subject', ''))
                self.keywords_edit.setText(result.get('Keywords', ''))
                
                # 启用编辑框
                self.title_edit.setEnabled(True)
                self.author_edit.setEnabled(True)
                self.subject_edit.setEnabled(True)
                self.keywords_edit.setEnabled(True)
        else:
            QMessageBox.warning(self, "警告", result)
            
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
            
    def update_metadata(self):
        """更新PDF元数据"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        metadata = {
            '/Title': self.title_edit.text(),
            '/Author': self.author_edit.text(),
            '/Subject': self.subject_edit.text(),
            '/Keywords': self.keywords_edit.text(),
            '/Producer': 'PDF工具',
            '/ModDate': datetime.datetime.now().strftime('D:%Y%m%d%H%M%S')
        }
        
        output_path = self.get_output_path("元数据")
        if output_path:
            success, message = PDFMetadata.set_metadata(
                self.input_file,
                output_path,
                metadata
            )
            if success:
                QMessageBox.information(self, "成功", message)
                # 更新当前文件和显示
                self.input_file = output_path
                self.file_label.setText(f"已选择: {output_path}")
                self.load_metadata()
            else:
                QMessageBox.critical(self, "错误", message)
                
    def encrypt_pdf(self):
        """加密PDF文件"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        # 获取密码
        user_password = self.user_password_edit.text()
        owner_password = self.owner_password_edit.text()
        
        # 如果都没有设置密码，提示用户
        if not user_password and not owner_password:
            QMessageBox.warning(self, "警告", "请至少设置一个密码")
            return
            
        # 获取权限设置
        permissions = {
            "print": self.print_cb.isChecked(),
            "modify": self.modify_cb.isChecked(),
            "copy": self.copy_cb.isChecked(),
            "annotate": self.annotate_cb.isChecked()
        }
        
        # 确认是否要直接修改源文件
        reply = QMessageBox.question(
            self,
            "确认",
            "是否要直接在源文件上添加加密？\n注意：此操作不可撤销",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 直接在源文件上加密
            success, message = PDFMetadata.add_encryption(
                self.input_file,
                self.input_file,  # 输入输出使用相同路径
                user_password,
                owner_password,
                permissions
            )
            if success:
                QMessageBox.information(self, "成功", message)
                # 清空密码输入框
                self.user_password_edit.clear()
                self.owner_password_edit.clear()
                # 更新文件标签，提示文件已加密
                self.file_label.setText(f"已选择(已加密): {self.input_file}")
                # 清空元数据显示
                self.metadata_label.setText("文件已加密，需要密码才能查看元数据")
            else:
                QMessageBox.critical(self, "错误", message)
        else:
            # 创建新文件
            output_path = self.get_output_path("加密")
            if output_path:
                success, message = PDFMetadata.add_encryption(
                    self.input_file,
                    output_path,
                    user_password,
                    owner_password,
                    permissions
                )
                if success:
                    QMessageBox.information(self, "成功", message)
                    # 清空密码输入框
                    self.user_password_edit.clear()
                    self.owner_password_edit.clear()
                    # 更新当前文件和显示
                    self.input_file = output_path
                    self.file_label.setText(f"已选择(已加密): {output_path}")
                    # 清空元数据显示
                    self.metadata_label.setText("文件已加密，需要密码才能查看元数据")
                else:
                    QMessageBox.critical(self, "错误", message) 
        
    def select_dict_file(self):
        """选择密码字典文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择密码字典文件",
            "",
            "文本文件 (*.txt)"
        )
        if file_path:
            self.dict_file_path = file_path
            self.dict_path_label.setText(f"已选择: {file_path}")
            
    def add_common_password(self):
        """添加常密码"""
        password = self.common_password_edit.text().strip()
        if password:
            if password not in self.common_passwords:
                self.common_passwords.append(password)
                self.common_passwords_label.setText(
                    "已添加的密码：\n" + "\n".join(self.common_passwords)
                )
            self.common_password_edit.clear()
            
    def crack_password(self):
        """开始破解密码"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
            
        # 显示进度对话框
        progress = QMessageBox(self)
        progress.setIcon(QMessageBox.Icon.Information)
        progress.setText("正在尝试破解密码，请稍候...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        
        # 尝试破解
        success, result = PDFMetadata.crack_password(
            self.input_file,
            self.dict_file_path,
            self.common_passwords
        )
        
        # 关闭进度对话框
        progress.close()
        
        if success:
            QMessageBox.information(self, "成功", f"找到密码：{result}")
        else:
            QMessageBox.warning(self, "提示", result) 
        
    def extract_content(self):
        """提取PDF内容"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
        
        # 获取输出路径
        output_path = self.get_output_path("提取")
        if not output_path:
            return
            
        # 显示进度对话框
        progress = QMessageBox()
        progress.setWindowTitle("提示")
        progress.setIcon(QMessageBox.Icon.Information)
        progress.setText("正在提取内容，请稍候...")
        progress.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress.show()
        
        try:
            # 尝试提取内容
            success, message = PDFMetadata.extract_content(self.input_file, output_path)
            
            # 确保进度对话框被关闭
            progress.done(0)
            
            if success:
                QMessageBox.information(self, "成功", message)
                # 更新当前文件和显示
                self.input_file = output_path
                self.file_label.setText(f"已选择: {output_path}")
                self.load_metadata()
            else:
                QMessageBox.critical(self, "错误", message)
        except Exception as e:
            # 确保进度对话框被关闭
            progress.done(0)
            QMessageBox.critical(self, "错误", str(e)) 