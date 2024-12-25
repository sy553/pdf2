from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_test_pdf(filename, text):
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, text)
    c.save()

def create_multi_page_pdf(filename, page_count):
    c = canvas.Canvas(filename, pagesize=letter)
    for i in range(page_count):
        c.drawString(100, 750, f"这是第 {i+1} 页")
        c.showPage()
    c.save()

def create_test_files():
    # 创建测试文件夹
    if not os.path.exists("test_files"):
        os.makedirs("test_files")
    
    # 创建三个测试PDF文件
    create_test_pdf("test_files/test1.pdf", "这是测试PDF文件1")
    create_test_pdf("test_files/test2.pdf", "这是测试PDF文件2")
    create_test_pdf("test_files/test3.pdf", "这是测试PDF文件3")
    
    # 创建一个10页的测试文件
    create_multi_page_pdf("test_files/multipage.pdf", 10)

if __name__ == "__main__":
    create_test_files()
    print("测试PDF文件已创建完成") 