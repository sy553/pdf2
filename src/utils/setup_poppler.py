import os
import sys
import shutil
import zipfile
import requests
import winreg
from pathlib import Path

def set_system_path(new_path):
    """
    将路径永久添加到系统环境变量
    """
    try:
        # 打开注册表
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 0, winreg.KEY_ALL_ACCESS) as key:
            # 获取当前PATH值
            current_path = winreg.QueryValueEx(key, 'Path')[0]
            
            # 检查路径是否已存在
            if new_path not in current_path:
                # 添加新路径
                new_value = current_path + os.pathsep + new_path
                winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_value)
                return True
            return True
    except Exception as e:
        print(f"设置系统环境变量失败: {str(e)}")
        return False

def download_poppler():
    """
    下载并安装Poppler
    """
    try:
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        # Poppler下载URL（Windows版本）
        poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.08.0-0/Release-23.08.0-0.zip"
        
        # 创建下载目录
        download_dir = os.path.join(project_root, 'downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        # 下载文件
        print("正在下载Poppler...")
        response = requests.get(poppler_url, stream=True)
        zip_path = os.path.join(download_dir, "poppler.zip")
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # 解压文件
        print("正在解压Poppler...")
        poppler_dir = os.path.join(project_root, 'poppler')
        if os.path.exists(poppler_dir):
            shutil.rmtree(poppler_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(poppler_dir)
        
        # 清理下载文件
        os.remove(zip_path)
        os.rmdir(download_dir)
        
        # 验证安装
        poppler_path = os.path.join(poppler_dir, 'Library', 'bin')
        if not os.path.exists(poppler_path):
            poppler_path = os.path.join(poppler_dir, 'bin')
        
        if os.path.exists(poppler_path):
            print(f"Poppler安装成功！路径: {poppler_path}")
            
            # 将Poppler路径添加到当前进程的环境变量
            if sys.platform.startswith('win'):
                path = os.environ.get('PATH', '')
                if poppler_path not in path:
                    os.environ['PATH'] = poppler_path + os.pathsep + path
                    print("Poppler已添加到当前进程PATH")
                    
                # 添加到系统环境变量
                if set_system_path(poppler_path):
                    print("Poppler已添加到系统环境变量")
                else:
                    print("警告：添加到系统环境变量失败，需要手动添加")
                    print(f"请将此路径添加到系统环境变量: {poppler_path}")
            
            return True
        else:
            print("Poppler安装失败！")
            return False
            
    except Exception as e:
        print(f"安装过程出错: {str(e)}")
        return False

if __name__ == "__main__":
    if not sys.platform.startswith('win'):
        print("此脚本仅支持Windows系统")
        sys.exit(1)
    
    # 检查是否具有管理员权限
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    
    if not is_admin:
        print("请以管理员权限运行此脚本")
        # 尝试重新以管理员权限运行
        if sys.platform.startswith('win'):
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(1)
    
    download_poppler() 