from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from PIL import Image
import os
import io

class PDFConverter:
    @staticmethod
    def images_to_pdf(image_paths, output_path, page_size='A4', margin=20):
        """
        将图片转换为PDF
        :param image_paths: 图片文件路径列表或PIL Image对象列表
        :param output_path: 输出PDF文件路径
        :param page_size: 页面大小 ('A4' 或 'letter')
        :param margin: 页面边距（像素）
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 选择页面大小
            if page_size.upper() == 'A4':
                pdf_size = A4
            else:
                pdf_size = letter
                
            # 创建PDF文档
            c = canvas.Canvas(output_path, pagesize=pdf_size)
            
            # 获取页面尺寸
            page_width, page_height = pdf_size
            
            # 计算可用区域（考虑边距）
            available_width = page_width - 2 * margin
            available_height = page_height - 2 * margin
            
            for image_source in image_paths:
                try:
                    # 处理图片
                    if isinstance(image_source, str):
                        # 如果是文件路径，打开图片
                        img = Image.open(image_source)
                    else:
                        # 如果是PIL Image对象，直接使用
                        img = image_source
                        
                    # 转换为RGB模式（如果需要）
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    
                    # 获取图片尺寸
                    img_width, img_height = img.size
                    
                    # 计算缩放比例
                    width_ratio = available_width / img_width
                    height_ratio = available_height / img_height
                    scale = min(width_ratio, height_ratio)
                    
                    # 计算缩放后的尺寸
                    new_width = img_width * scale
                    new_height = img_height * scale
                    
                    # 计算居中位置
                    x = margin + (available_width - new_width) / 2
                    y = margin + (available_height - new_height) / 2
                    
                    # 将图片保存为临时文件
                    temp_path = f"temp_{os.getpid()}.jpg"
                    img = img.resize((int(new_width), int(new_height)), Image.Resampling.LANCZOS)
                    img.save(temp_path, "JPEG", quality=95)
                    
                    # 在PDF中绘制图片
                    c.drawImage(temp_path, x, y, width=new_width, height=new_height)
                    
                    # 删除临时文件
                    os.remove(temp_path)
                    
                    # 添加新页面（除了最后一张图片）
                    if image_source != image_paths[-1]:
                        c.showPage()
                        
                except Exception as e:
                    print(f"处理图片时出错: {str(e)}")
                    continue
            
            # 保存PDF
            c.save()
            
            return True, f"成功将 {len(image_paths)} 张图片转换为PDF"
            
        except Exception as e:
            return False, f"转换失败: {str(e)}"
            
    @staticmethod
    def pdf_to_images(input_path, output_dir, format='PNG', dpi=200, first_page=None, last_page=None):
        """
        将PDF文件转换为图片
        :param input_path: 输入PDF文件路径
        :param output_dir: 输出目录路径
        :param format: 输出图片格式 ('PNG' 或 'JPEG')
        :param dpi: 输出图片的DPI（分辨率）
        :param first_page: 起始页码（从1开始），None表示从第一页开始
        :param last_page: 结束页码，None表示到最后一页
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # 获取文件名（不包含扩展名）
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            
            # 设置poppler路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            poppler_path = os.path.join(project_root, 'poppler', 'Library', 'bin')
            
            if not os.path.exists(poppler_path):
                # 尝试其他可能的路径
                poppler_path = os.path.join(project_root, 'poppler', 'bin')
                
            if not os.path.exists(poppler_path):
                return False, "未找到poppler，请确保已正确安装poppler"
                
            # 转换PDF为图片
            images = convert_from_path(
                input_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                poppler_path=poppler_path
            )
            
            # 保存图片
            for i, image in enumerate(images, start=1):
                # 如果指定了起始页码，调整文件名中的页码
                page_num = i if first_page is None else first_page + i - 1
                output_path = os.path.join(
                    output_dir,
                    f"{base_name}_第{page_num}页.{format.lower()}"
                )
                
                # 如果是JPEG格式，转换为RGB模式��去除alpha通道）
                if format.upper() == 'JPEG':
                    image = image.convert('RGB')
                
                image.save(output_path, format=format)
            
            return True, f"转换完成，共生成{len(images)}个图片文件"
            
        except Exception as e:
            return False, f"转换失败: {str(e)}"
            
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
                
            # 使用PyPDF2获取页数
            reader = PdfReader(pdf_path)
            return True, len(reader.pages)
            
        except Exception as e:
            return False, f"获取页数失败: {str(e)}" 