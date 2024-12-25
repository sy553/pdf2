from PyPDF2 import PdfReader, PdfWriter
import os

class PDFSplitter:
    @staticmethod
    def split_pdf(input_path, output_dir, page_groups, separate_files=False):
        """
        从PDF文件中提取指定页面
        :param input_path: 输入PDF文件路径
        :param output_dir: 输出目录路径
        :param page_groups: 页面组列表，每组是一个页码列表 [[1,2,3], [5,6,7]]
        :param separate_files: 是否将每页保存为单独的文件
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            reader = PdfReader(input_path)
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            # 检查页码是否有效
            max_page = len(reader.pages)
            for group in page_groups:
                for page_num in group:
                    if page_num < 1 or page_num > max_page:
                        return False, f"页码 {page_num} 超出范围 (1-{max_page})"
            
            if separate_files:
                # 每页保存为单独的文件
                for group in page_groups:
                    for page_num in group:
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num - 1])
                        output_path = os.path.join(output_dir, f"{base_name}_第{page_num}页.pdf")
                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)
            else:
                # 每组页面保存为一个文件
                for i, group in enumerate(page_groups):
                    writer = PdfWriter()
                    for page_num in group:
                        writer.add_page(reader.pages[page_num - 1])
                    # 生成描述性文件名
                    page_range = f"{min(group)}-{max(group)}"
                    output_path = os.path.join(output_dir, f"{base_name}_第{page_range}页.pdf")
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
            
            return True, "页面提取成功"
            
        except Exception as e:
            return False, f"页面提取失败: {str(e)}"
            
    @staticmethod
    def get_pdf_page_count(pdf_path):
        """
        获取PDF文件的总页数
        :param pdf_path: PDF文件路径
        :return: (bool, int|str) - (是否成功, 页数|错误信息)
        """
        try:
            if not os.path.exists(pdf_path):
                return False, "文件不存在"
                
            reader = PdfReader(pdf_path)
            return True, len(reader.pages)
            
        except Exception as e:
            return False, f"获取页数失败: {str(e)}" 