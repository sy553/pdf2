import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow

@pytest.fixture
def app(qtbot):
    """创建应用实例"""
    test_app = QApplication([])
    return test_app

@pytest.fixture
def main_window(app, qtbot):
    """创建主窗口实例"""
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_window_title(main_window):
    """测试窗口标题"""
    assert main_window.windowTitle() == 'PDF工具箱'

def test_initial_state(main_window):
    """测试初始状态"""
    # 测试窗口最小尺寸
    assert main_window.minimumSize().width() == 800
    assert main_window.minimumSize().height() == 600
    
    # 测试状态栏初始消息
    assert main_window.statusBar().currentMessage() == '就绪'

def test_menu_creation(main_window):
    """测试菜单创建"""
    menubar = main_window.menuBar()
    
    # 测试主要菜单项是否存在
    menus = [menu.title() for menu in menubar.findChildren(menubar.findChildren(menubar.__class__)[0].__class__)]
    assert '文件' in menus
    assert '页面管理' in menus
    assert '帮助' in menus

def test_file_selection(main_window, qtbot, tmp_path):
    """测试文件选择功能"""
    # 创建测试PDF文件
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b'%PDF-1.4')  # 创建一个最小的PDF文件
    
    # 模拟文件选择
    main_window.watermark_input_path.setText(str(test_file))
    assert main_window.watermark_input_path.text() == str(test_file)

def test_watermark_validation(main_window, qtbot):
    """测试水印验证"""
    # 测试空输入验证
    with pytest.raises(Exception):
        main_window.add_watermark()
    
    # 测试水印文字验证
    main_window.watermark_text.setText("")
    with pytest.raises(Exception):
        main_window.add_watermark()

def test_compress_validation(main_window, qtbot):
    """测试压缩验证"""
    # 测试空输入验证
    with pytest.raises(Exception):
        main_window.compress_pdf()
    
    # 测试压缩质量范围
    assert main_window.compress_quality.minimum() == 1
    assert main_window.compress_quality.maximum() == 3

def test_page_management(main_window, qtbot):
    """测试页面管理功能"""
    # 测试分割模式切换
    main_window.split_mode.setCurrentIndex(1)
    assert main_window.pages_per_file_widget.isVisible()
    
    main_window.split_mode.setCurrentIndex(2)
    assert main_window.split_params_widget.isVisible()
    
    main_window.split_mode.setCurrentIndex(3)
    assert main_window.selective_split_widget.isVisible()

def test_drag_drop_support(main_window, qtbot):
    """测试拖放支持"""
    # 测试缩略图拖放
    if hasattr(main_window, 'reorder_thumbnails'):
        thumb_list = main_window.reorder_thumbnails
        assert thumb_list.acceptDrops()

def test_progress_bars(main_window):
    """测试进度条"""
    # 测试各个进度条的初始状态
    assert not main_window.watermark_progress.isVisible()
    assert not main_window.compress_progress.isVisible()
    assert not main_window.convert_progress.isVisible()
    assert not main_window.split_progress.isVisible()
    assert not main_window.merge_progress.isVisible()
    assert not main_window.reorder_progress.isVisible() 