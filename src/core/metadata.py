from PyPDF2 import PdfReader, PdfWriter
import datetime
import os
import subprocess

class PDFMetadata:
    @staticmethod
    def get_metadata(input_path):
        """
        获取PDF文件的元数据
        :param input_path: 输入PDF文件路径
        :return: (bool, dict|str) - (是否成功, 元数据字典|错误信息)
        """
        try:
            reader = PdfReader(input_path)
            metadata = {}
            
            # 检查是否加密
            if reader.is_encrypted:
                metadata['Encrypted'] = True
                metadata['FileSize'] = os.path.getsize(input_path)
                # 转换为合适的单位
                size_bytes = metadata['FileSize']
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024:
                        metadata['FileSize'] = f"{size_bytes:.2f} {unit}"
                        break
                    size_bytes /= 1024
                return True, metadata
            
            # 获取基本元数据
            if reader.metadata:
                for key, value in reader.metadata.items():
                    # 移除/前缀
                    clean_key = key[1:] if key.startswith('/') else key
                    metadata[clean_key] = value
            
            # 获取页数
            metadata['Pages'] = len(reader.pages)
            
            # 获取文件大小
            size_bytes = os.path.getsize(input_path)
            # 转换为合适的单位
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    metadata['FileSize'] = f"{size_bytes:.2f} {unit}"
                    break
                size_bytes /= 1024
            
            return True, metadata
            
        except Exception as e:
            return False, f"获取元数据失败: {str(e)}"
    
    @staticmethod
    def set_metadata(input_path, output_path, metadata):
        """
        设置PDF文件的元数据
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :param metadata: 元数据字典
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)
            
            # 添加元数据
            writer.add_metadata(metadata)
            
            # 保存文件
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True, "元数据修改成功"
            
        except Exception as e:
            return False, f"修改元数据失败: {str(e)}"
    
    @staticmethod
    def add_encryption(input_path, output_path, user_password=None, owner_password=None, 
                      permissions=None):
        """
        为PDF添加密码保护
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径（可以与输入路径相同）
        :param user_password: 用户密码（打开文档密码）
        :param owner_password: 所有者密码（编辑文档密码）
        :param permissions: 权限设置字典
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # 复制所有页面
            for page in reader.pages:
                writer.add_page(page)
            
            # 设置默认权限
            if permissions is None:
                permissions = {
                    "print": True,           # 允许打印
                    "modify": False,         # 禁止修改
                    "copy": True,            # 允许复制内容
                    "annotate": False,       # 禁止添加注释
                }
            
            # 计算权限掩码
            # 使用标准PDF权限掩码值
            permission_mask = 0
            if permissions.get("print", True):
                permission_mask |= 4  # 打印文档
            if permissions.get("modify", False):
                permission_mask |= 8  # 修改内容
            if permissions.get("copy", True):
                permission_mask |= 16  # 复制内容
            if permissions.get("annotate", False):
                permission_mask |= 32  # 添加注释
            
            # 加密PDF
            writer.encrypt(
                user_password=user_password if user_password else "",
                owner_password=owner_password if owner_password else (user_password if user_password else ""),
                use_128bit=True,
                permissions_flag=permission_mask
            )
            
            # 保存文件
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True, "加密设置成功"
            
        except Exception as e:
            return False, f"加密设置失败: {str(e)}"
    
    @staticmethod
    def crack_password(input_path, password_file=None, common_passwords=None):
        """
        尝试破解PDF密码
        :param input_path: 输入PDF文件路径
        :param password_file: 密码字典文件路径
        :param common_passwords: 常用密码列表
        :return: (bool, str) - (是否成功, 成功则返回密码，失败则返回错误信息)
        """
        try:
            # 创建一个密码列表
            passwords = []
            
            # 添加常用密码
            if common_passwords:
                passwords.extend(common_passwords)
            
            # 从密码字典文件中读取密码
            if password_file and os.path.exists(password_file):
                with open(password_file, 'r', encoding='utf-8') as f:
                    passwords.extend([line.strip() for line in f if line.strip()])
            
            # 如果没有提供任何密码，使用一些默认的常用密码
            if not passwords:
                passwords = [
                    "", "123456", "password", "admin", "12345678", "123456789", "1234567890",
                    "abc123", "qwerty", "111111", "123123", "admin123", "root", "666666",
                    "888888", "password123", "1234", "12345", "000000", "abc123456"
                ]
            
            # 尝试打开PDF文件
            reader = PdfReader(input_path)
            
            # 如果PDF没有加密，返回提示
            if not reader.is_encrypted:
                return False, "此PDF文件没有加密"
            
            # 尝试每个密码
            for password in passwords:
                try:
                    # 尝试解密
                    if reader.decrypt(password) > 0:
                        return True, password
                except:
                    continue
            
            return False, "未能找到正确的密码"
            
        except Exception as e:
            return False, f"破解过程出错: {str(e)}"
    
    @staticmethod
    def extract_content(input_path, output_path):
        """
        提取加密PDF的内容并创建新的PDF
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :return: (bool, str) - (是否成功, 成功/错误信息)
        """
        try:
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # 如果文件没有加密，直接复制
            if not reader.is_encrypted:
                for page in reader.pages:
                    writer.add_page(page)
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                return True, "内容提取成功"
            
            # 常用密码组合方式
            common_elements = {
                'years': [str(year) for year in range(1960, 2024)],
                'numbers': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
                'special': ['!', '@', '#', '$', '%', '&', '*'],
                'common_words': ['admin', 'password', 'pass', 'pwd', '123', 'abc', 'qwerty', 
                               'adobe', 'test', 'master', 'root', 'pdf'],
                'common_passwords': [
                    '', '123456', 'password', '12345678', '123456789', 'admin123',
                    '1234567890', '000000', '111111', '88888888', '12345', '1234',
                    'admin', 'root', '123123', '666666', '888888', 'abc123'
                ]
            }
            
            def try_password(pwd):
                try:
                    reader = PdfReader(input_path)
                    if reader.decrypt(pwd) > 0:
                        # 密码正确，复制所有页面
                        writer = PdfWriter()
                        for page in reader.pages:
                            writer.add_page(page)
                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)
                        return True
                except:
                    return False
                return False
            
            # 1. 首先尝试常用密码
            for pwd in common_elements['common_passwords']:
                if try_password(pwd):
                    return True, f"破解成功，密码为: {pwd if pwd else '空密码'}"
            
            # 2. 尝试年份组合
            for year in common_elements['years']:
                # 单独年份
                if try_password(year):
                    return True, f"破解成功，密码为: {year}"
                # 年份+特殊字符
                for special in common_elements['special']:
                    if try_password(year + special):
                        return True, f"破解成功，密码为: {year + special}"
            
            # 3. 尝试常用词+数字组合
            for word in common_elements['common_words']:
                if try_password(word):
                    return True, f"破解成功，密码为: {word}"
                # 常用词+年份后两位
                for year in range(0, 100):
                    year_str = f"{year:02d}"
                    pwd = word + year_str
                    if try_password(pwd):
                        return True, f"破解成功，密码为: {pwd}"
            
            # 4. 尝试4-8位纯数字组合
            for length in range(4, 9):
                for num in range(10 ** (length - 1), min(10 ** length, 100000)):  # 限制尝试次数
                    pwd = str(num)
                    if try_password(pwd):
                        return True, f"破解成功，密码为: {pwd}"
            
            # 如果所有尝试都失败，返回错误信息
            return False, "无法破解此PDF的密码，可能使用了复杂密码"
            
        except Exception as e:
            return False, f"破解过程出错: {str(e)}" 