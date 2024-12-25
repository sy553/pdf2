import os
import pytest
from PyPDF2 import PdfReader
from src.core.editor import PDFEditor

# 测试文件路径
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'test_files')
if not os.path.exists(TEST_FILES_DIR):
    os.makedirs(TEST_FILES_DIR)

@pytest.fixture
def sample_pdf():
    """创建一个测试用的PDF文件"""
    pdf_path = os.path.join(TEST_FILES_DIR, 'sample.pdf')
    if not os.path.exists(pdf_path):
        # 使用reportlab创建测试PDF
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "测试文档")
        c.showPage()
        c.save()
    return pdf_path

def test_get_pdf_page_count(sample_pdf):
    """测试获取PDF页数"""
    count = PDFEditor.get_pdf_page_count(sample_pdf)
    assert count == 1

def test_add_watermark(sample_pdf):
    """测试添加水印"""
    output_path = os.path.join(TEST_FILES_DIR, 'watermark.pdf')
    success, message = PDFEditor.add_watermark(
        sample_pdf,
        output_path,
        "测试水印",
        0.5,
        45
    )
    assert success
    assert os.path.exists(output_path)
    # 验证水印PDF是否可以正常打开
    reader = PdfReader(output_path)
    assert len(reader.pages) == 1

def test_remove_watermark(sample_pdf):
    """测试移除水印"""
    output_path = os.path.join(TEST_FILES_DIR, 'no_watermark.pdf')
    success, message = PDFEditor.remove_watermark(
        sample_pdf,
        output_path
    )
    assert success
    assert os.path.exists(output_path)
    # 验证处理后的PDF是否可以正常打开
    reader = PdfReader(output_path)
    assert len(reader.pages) == 1

def test_compress_pdf(sample_pdf):
    """测试PDF压缩"""
    output_path = os.path.join(TEST_FILES_DIR, 'compressed.pdf')
    success, message = PDFEditor.compress_pdf(
        sample_pdf,
        output_path,
        quality='medium'
    )
    assert success
    assert os.path.exists(output_path)
    # 验证压缩后的文件大小是否小于等于原文件
    assert os.path.getsize(output_path) <= os.path.getsize(sample_pdf)

def test_split_pdf(sample_pdf):
    """测试PDF分割"""
    output_dir = os.path.join(TEST_FILES_DIR, 'split')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    success, message = PDFEditor.split_pdf(
        sample_pdf,
        output_dir
    )
    assert success
    # 验证是否生成了分割后��文件
    assert len(os.listdir(output_dir)) > 0

def test_merge_pdfs(sample_pdf):
    """测试PDF合并"""
    output_path = os.path.join(TEST_FILES_DIR, 'merged.pdf')
    success, message = PDFEditor.merge_pdfs(
        [sample_pdf, sample_pdf],
        output_path
    )
    assert success
    assert os.path.exists(output_path)
    # 验证合并后的页数是否正确
    reader = PdfReader(output_path)
    assert len(reader.pages) == 2

def test_reorder_pages(sample_pdf):
    """测试页面重排序"""
    # 先创建一个多页PDF用于测试
    multi_page_pdf = os.path.join(TEST_FILES_DIR, 'multi_page.pdf')
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(multi_page_pdf)
    for i in range(3):
        c.drawString(100, 750, f"第{i+1}页")
        c.showPage()
    c.save()
    
    output_path = os.path.join(TEST_FILES_DIR, 'reordered.pdf')
    success, message = PDFEditor.reorder_pages(
        multi_page_pdf,
        output_path,
        "3,1,2"
    )
    assert success
    assert os.path.exists(output_path)
    # 验证页数是否正确
    reader = PdfReader(output_path)
    assert len(reader.pages) == 3

def test_add_page_numbers(sample_pdf):
    """测试添加页码"""
    output_path = os.path.join(TEST_FILES_DIR, 'with_numbers.pdf')
    success, message = PDFEditor.add_page_numbers(
        sample_pdf,
        output_path,
        start_number=1,
        position='bottom'
    )
    assert success
    assert os.path.exists(output_path)
    # 验证处理后的PDF是否可以正常打开
    reader = PdfReader(output_path)
    assert len(reader.pages) == 1 