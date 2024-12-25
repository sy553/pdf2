import os
import sys
import pytest
import subprocess
from datetime import datetime

def run_tests():
    """运行测试并生成报告"""
    # 创建测试报告目录
    report_dir = "test_reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # 生成报告文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"test_report_{timestamp}.txt")
    
    print("开始运行测试...")
    print("=" * 50)
    
    try:
        # 运行测试并收集输出
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("PDF工具箱测试报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            
            # 运行pytest并捕获输出
            result = subprocess.run(
                ["pytest", "-v", "--cov=src", "--cov-report=html"],
                capture_output=True,
                text=True
            )
            
            # 写入测试结果
            f.write("测试输出:\n")
            f.write(result.stdout)
            
            if result.stderr:
                f.write("\n错误信息:\n")
                f.write(result.stderr)
            
            # 检查覆盖率报告
            if os.path.exists("htmlcov/index.html"):
                f.write("\n覆盖率报告已生成: htmlcov/index.html\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"测试{'成功' if result.returncode == 0 else '失败'}\n")
    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        return False
    
    print(f"测试完成，报告已保存到: {report_file}")
    print("覆盖率报告位置: htmlcov/index.html")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1) 