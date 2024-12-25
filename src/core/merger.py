from PyPDF2 import PdfMerger
import os

class PDFMerger:
    @staticmethod
    def merge_pdfs(pdf_files, output_path):
        """
        合并多个PDF文件
        :param pdf_files: PDF文件路径列表
        :param output_path: 输出文件路径
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            merger = PdfMerger()
            
            # 检查所有文件是否存在
            for pdf_file in pdf_files:
                if not os.path.exists(pdf_file):
                    return False, f"文件不存在: {pdf_file}"
            
            # 添加所有PDF文件
            for pdf_file in pdf_files:
                merger.append(pdf_file)
            
            # 保存合并后的文件
            merger.write(output_path)
            merger.close()
            
            return True, "合并成功"
            
        except Exception as e:
            return False, f"合并失败: {str(e)}" 