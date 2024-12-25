from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import io
import pikepdf
from reportlab.lib.colors import black

class PDFEditor:
    # 注册中文字体
    try:
        # 尝试注册系统中的微软雅黑字体
        font_path = "C:/Windows/Fonts/msyh.ttc"
        pdfmetrics.registerFont(TTFont('MicrosoftYaHei', font_path))
        DEFAULT_FONT = 'MicrosoftYaHei'
    except:
        try:
            # 如果没有微软雅黑，尝试注册宋体
            font_path = "C:/Windows/Fonts/simsun.ttc"
            pdfmetrics.registerFont(TTFont('SimSun', font_path))
            DEFAULT_FONT = 'SimSun'
        except:
            # 如果都没有，使用默认的Helvetica字体
            DEFAULT_FONT = 'Helvetica'

    @staticmethod
    def remove_watermark(input_path, output_path):
        """
        移除PDF水印
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                return False, "输入文件不存在"

            # 使用pikepdf打开PDF
            pdf = pikepdf.Pdf.open(input_path)
            
            # 清理透明对象和图层
            for page in pdf.pages:
                if page.get('/Resources'):
                    # 处理XObject
                    if '/XObject' in page.Resources:
                        xobjects = page.Resources.XObject
                        keys_to_remove = []
                        
                        for key, xobject in xobjects.items():
                            if isinstance(xobject, pikepdf.Dictionary):
                                # 检查是否是水印层
                                if any(str(xobject.get(k, '')).lower().find('watermark') >= 0 
                                      for k in xobject.keys()):
                                    keys_to_remove.append(key)
                                elif ('/Subtype' in xobject and str(xobject.Subtype) in ['/Form', '/Image']) or \
                                     ('/Type' in xobject and str(xobject.Type) in ['/Watermark', '/Stamp', '/Background']):
                                    keys_to_remove.append(key)
                                    # 检查透明度
                                elif '/Resources' in xobject:
                                    if '/ExtGState' in xobject.Resources:
                                        for gs in xobject.Resources.ExtGState.values():
                                            if isinstance(gs, pikepdf.Dictionary):
                                                if '/ca' in gs and float(str(gs.ca)) < 1.0:
                                                    keys_to_remove.append(key)
                                                    break
                                                if '/CA' in gs and float(str(gs.CA)) < 1.0:
                                                    keys_to_remove.append(key)
                                                    break
                        
                        # 移除水印对象
                        for key in keys_to_remove:
                            try:
                                del xobjects[key]
                            except:
                                pass
                    
                    # 处理内容流
                    if page.get('/Contents'):
                        contents = page.Contents
                        if isinstance(contents, pikepdf.Array):
                            new_contents = pikepdf.Array()
                            for content in contents:
                                try:
                                    stream = content.read_bytes()
                                    # 移除水印相关操作
                                    replacements = [
                                        (b'/Watermark', b'/Artifact'),
                                        (b'/Stamp', b'/Artifact'),
                                        (b'/Background', b'/Artifact'),
                                        (b'/Overlay', b'/Artifact'),
                                        (b'/Underlay', b'/Artifact'),
                                        (b'gs', b'n'),
                                        (b'GS', b'n'),
                                        (b'Gs', b'n'),
                                        (b'BMC', b'BDC /Artifact'),
                                        (b'BDC', b'BDC /Artifact'),
                                        (b'EMC', b'EMC'),
                                        (b'BM /Normal', b'BM /Compatible'),
                                        (b'BM /Multiply', b'BM /Normal'),
                                        (b'BM /Screen', b'BM /Normal'),
                                        (b'BM /Overlay', b'BM /Normal'),
                                        (b'BM /Darken', b'BM /Normal'),
                                        (b'BM /Lighten', b'BM /Normal'),
                                        (b'SMask', b'Artifact'),
                                    ]
                                    for old, new in replacements:
                                        stream = stream.replace(old, new)
                                    new_contents.append(pikepdf.Stream(pdf, stream))
                                except Exception:
                                    new_contents.append(content)
                            page.Contents = new_contents
                        elif isinstance(contents, pikepdf.Stream):
                            try:
                                stream = contents.read_bytes()
                                # 应用相同的替换
                                replacements = [
                                    (b'/Watermark', b'/Artifact'),
                                    (b'/Stamp', b'/Artifact'),
                                    (b'/Background', b'/Artifact'),
                                    (b'/Overlay', b'/Artifact'),
                                    (b'/Underlay', b'/Artifact'),
                                    (b'gs', b'n'),
                                    (b'GS', b'n'),
                                    (b'Gs', b'n'),
                                    (b'BMC', b'BDC /Artifact'),
                                    (b'BDC', b'BDC /Artifact'),
                                    (b'EMC', b'EMC'),
                                    (b'BM /Normal', b'BM /Compatible'),
                                    (b'BM /Multiply', b'BM /Normal'),
                                    (b'BM /Screen', b'BM /Normal'),
                                    (b'BM /Overlay', b'BM /Normal'),
                                    (b'BM /Darken', b'BM /Normal'),
                                    (b'BM /Lighten', b'BM /Normal'),
                                    (b'SMask', b'Artifact'),
                                ]
                                for old, new in replacements:
                                    stream = stream.replace(old, new)
                                page.Contents = pikepdf.Stream(pdf, stream)
                            except Exception:
                                pass
                    
                    # 处理扩展图形状态
                    if '/ExtGState' in page.Resources:
                        extgstate = page.Resources.ExtGState
                        keys_to_remove = []
                        
                        for key, gs in extgstate.items():
                            if isinstance(gs, pikepdf.Dictionary):
                                try:
                                    # 移除透明度设置
                                    if '/ca' in gs:
                                        del gs['/ca']
                                    if '/CA' in gs:
                                        del gs['/CA']
                                    if '/AIS' in gs:
                                        del gs['/AIS']
                                    if '/BM' in gs:
                                        del gs['/BM']
                                    if '/SMask' in gs:
                                        del gs['/SMask']
                                    # 如果图形状态为空，标记为删除
                                    if len(gs.keys()) == 0:
                                        keys_to_remove.append(key)
                                except Exception:
                                    continue
                        
                        # 移除空的图形状态
                        for key in keys_to_remove:
                            try:
                                del extgstate[key]
                            except:
                                pass
                    
                    # 处理Properties（通常包含水印设置）
                    if '/Properties' in page.Resources:
                        try:
                            del page.Resources['/Properties']
                        except:
                            pass
            
            # 移除文档级别的设置
            for key in ['/OCProperties', '/Metadata', '/MarkInfo']:
                if key in pdf.Root:
                    try:
                        del pdf.Root[key]
                    except:
                        pass
            
            # 保存处理后的文件，使用最大压缩
            pdf.save(output_path,
                    compress_streams=True,
                    preserve_pdfa=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate,
                    stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
            pdf.close()
            
            # 尝试二次处理
            try:
                pdf = pikepdf.Pdf.open(output_path)
                pdf.save(output_path,
                        compress_streams=True,
                        preserve_pdfa=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate,
                        stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
                pdf.close()
            except:
                pass
            
            return True, "水印清理完成"
            
        except Exception as e:
            return False, f"水印处理失败: {str(e)}"
    
    @staticmethod
    def add_watermark(input_path, output_path, watermark_text, opacity=0.3, angle=45):
        """
        添加文字水印
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :param watermark_text: 水印文字
        :param opacity: 水印透明度 (0-1)
        :param angle: 旋转角度
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 创建水印PDF
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            c.saveState()
            
            # 获取页面尺寸
            reader = PdfReader(input_path)
            if reader.pages:
                # 获取第一页的尺寸
                page = reader.pages[0]
                mediabox = page.mediabox
                page_width = float(mediabox.width)
                page_height = float(mediabox.height)
            else:
                page_width = float(letter[0])
                page_height = float(letter[1])
            
            # 创建画布使用实际页面尺寸
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.saveState()
            
            # 移动到页面中心
            c.translate(page_width/2, page_height/2)
            c.rotate(angle)
            c.setFillAlpha(float(opacity))
            
            # 设置字体和大小
            font_size = min(page_width, page_height) / 10  # 根据页面大小调整字体大小
            c.setFont(PDFEditor.DEFAULT_FONT, font_size)
            
            # 绘制水印文字
            c.setFillGray(0.5)  # 设置水印颜色为灰色
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
            c.save()
            
            # 移动到开始位置
            packet.seek(0)
            watermark = PdfReader(packet)
            watermark_page = watermark.pages[0]
            
            # 读取原始PDF
            writer = PdfWriter()
            
            # 为每一页添加水印
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # 保存结果
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
            return True, "水印添加成功"
            
        except Exception as e:
            return False, f"添加水印失败: {str(e)}"
    
    @staticmethod
    def compress_pdf(input_path, output_path, quality='medium', image_dpi=None):
        """
        压缩PDF文件
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :param quality: 压缩质量 ('low', 'medium', 'high')
        :param image_dpi: 图片DPI，None表示保持原始DPI
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                return False, "输入文件不存在"

            # 使用pikepdf打开PDF
            pdf = pikepdf.Pdf.open(input_path)
            
            # 处理每一页
            for page in pdf.pages:
                if page.get('/Resources'):
                    # 处理图片
                    if '/XObject' in page.Resources:
                        xobjects = page.Resources.XObject
                        for key, xobject in list(xobjects.items()):  # 使用list()创建副本进行迭代
                            try:
                                if isinstance(xobject, pikepdf.Dictionary) and xobject.get('/Subtype') == '/Image':
                                    # 如果是图片，进行压缩
                                    if image_dpi is not None and image_dpi != 72:  # 72 DPI是PDF的标分辨率
                                        try:
                                            # 获取原始尺寸
                                            orig_w = int(xobject.get('/Width', 0))
                                            orig_h = int(xobject.get('/Height', 0))
                                            
                                            if orig_w > 0 and orig_h > 0:
                                                # 计算新尺寸
                                                scale = image_dpi / 72.0
                                                new_w = max(1, int(orig_w * scale))
                                                new_h = max(1, int(orig_h * scale))
                                                
                                                # 更新图片尺寸
                                                if new_w != orig_w or new_h != orig_h:
                                                    xobject['/Width'] = new_w
                                                    xobject['/Height'] = new_h
                                        except Exception as e:
                                            print(f"处理图片尺寸时出错: {str(e)}")
                                            continue
                            except Exception as e:
                                print(f"处理XObject时出错: {str(e)}")
                                continue
            
            # 根据质量设置压缩参数
            if quality == 'low':
                # 最大压缩
                pdf.save(output_path,
                        compress_streams=True,
                        preserve_pdfa=False,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate,
                        stream_decode_level=pikepdf.StreamDecodeLevel.none)
            elif quality == 'medium':
                # 平衡压缩
                pdf.save(output_path,
                        compress_streams=True,
                        preserve_pdfa=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate,
                        stream_decode_level=pikepdf.StreamDecodeLevel.generalized)
            else:  # high
                # 最小压缩
                pdf.save(output_path,
                        compress_streams=True,
                        preserve_pdfa=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.preserve,
                        stream_decode_level=pikepdf.StreamDecodeLevel.specialized)
            
            # 计算压缩比例
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = ((original_size - compressed_size) / original_size) * 100
            
            if compression_ratio <= 0:
                return True, "文件已经是最优大小无需进一步压缩"
            
            return True, f"压缩成功！压缩率：{compression_ratio:.1f}%"
            
        except Exception as e:
            return False, f"压缩失败: {str(e)}" 
    
    @staticmethod
    def pdf_to_images(input_path, output_dir, image_format='png', dpi=300):
        """
        将PDF转换为图片
        :param input_path: 输入PDF文件路径
        :param output_dir: 输出目录路径
        :param image_format: 图片格式 ('png', 'jpeg', 'tiff')
        :param dpi: 图片DPI
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
            
            # 检查输出目录是否存在，不存在则创建
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 使用pdf2image进行转换
            from pdf2image import convert_from_path
            
            # 转换PDF为图片
            images = convert_from_path(
                input_path,
                dpi=dpi,
                fmt=image_format,
                output_folder=output_dir,
                output_file=os.path.splitext(os.path.basename(input_path))[0],
                paths_only=True,
                poppler_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'poppler', 'bin')
            )
            
            # 返回成功信息
            return True, f"转换完成，生成{len(images)}张图片"
            
        except Exception as e:
            return False, f"转换失败: {str(e)}" 

    @staticmethod
    def images_to_pdf(input_paths, output_path, page_size='A4', margin=10):
        """
        将图片转换为PDF
        :param input_paths: 输入图片文件路径列表
        :param output_path: 输出PDF文件路径
        :param page_size: 页面大小 ('A4', 'Letter', '自动')
        :param margin: 页边距（毫米）
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            from PIL import Image
            from reportlab.lib.pagesizes import A4, letter
            from reportlab.lib.units import mm
            
            # 创建PDF写入器
            writer = PdfWriter()
            
            # 处理每个图片
            for img_path in input_paths:
                # 打开图片
                img = Image.open(img_path)
                
                # 转换为RGB模式（如果是RGBA，去除透明通道）
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 确定页面大小
                if page_size == 'A4':
                    page_width, page_height = A4
                elif page_size == 'Letter':
                    page_width, page_height = letter
                else:  # 自动
                    # 根据图片尺寸和DPI计算页面大小
                    img_width_mm = img.width * 25.4 / img.info.get('dpi', (72, 72))[0]
                    img_height_mm = img.height * 25.4 / img.info.get('dpi', (72, 72))[1]
                    page_width = img_width_mm * mm + 2 * margin * mm
                    page_height = img_height_mm * mm + 2 * margin * mm
                
                # 创建临时的PDF文件
                img_temp = io.BytesIO()
                img.save(img_temp, format='PDF', resolution=72.0)
                img_temp.seek(0)
                
                # 读取临时PDF并添加到写入器
                reader = PdfReader(img_temp)
                if reader.pages:
                    writer.add_page(reader.pages[0])
                
                img_temp.close()
            
            # 保存最终的PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
                
            return True, f"转换成功，处理{len(input_paths)}张图片"
            
        except Exception as e:
            return False, f"转换失败: {str(e)}" 

    @staticmethod
    def get_pdf_page_count(input_path):
        """
        获取PDF文件的总页数
        :param input_path: 输入PDF文件路径
        :return: 总页数
        """
        try:
            # 先尝试使用 pikepdf 打开
            try:
                with pikepdf.Pdf.open(input_path, allow_overwriting_input=True) as pdf:
                    return len(pdf.pages)
            except pikepdf.PasswordError:
                # 如果文件有密码保护，尝试使用 PyPDF2
                with open(input_path, 'rb') as file:
                    reader = PdfReader(file)
                    if reader.is_encrypted:
                        # 如果是加密的PDF，尝试使用空密码
                        try:
                            reader.decrypt('')
                        except:
                            raise Exception("PDF文件受密码保护")
                    return len(reader.pages)
        except Exception as e:
            raise Exception(f"获取页数失败: {str(e)}")
    
    @staticmethod
    def split_pdf(input_path, output_dir, page_groups=None):
        """
        分割PDF文件
        :param input_path: 输入PDF文件路径
        :param output_dir: 输出目录
        :param page_groups: 页面组列表，每个元素可以是页码范围字符串，如 "1-3,5,7-9"
        :return: (success, message)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
            
            # 创建输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 打开PDF文件
            with pikepdf.Pdf.open(input_path) as pdf:
                total_pages = len(pdf.pages)
                
                if page_groups is None:
                    # 单页拆分模式
                    for i in range(total_pages):
                        with pikepdf.Pdf.new() as new_pdf:
                            new_pdf.pages.append(pdf.pages[i])
                            output_path = os.path.join(output_dir, f"page_{i+1}.pdf")
                            new_pdf.save(output_path)
                    return True, f"已将PDF分割��{total_pages}个单页文件"
                
                # 处理页面组
                for i, group in enumerate(page_groups):
                    pages_to_extract = []
                    # 处理页码范围字符串
                    ranges = group.split(',')
                    for r in ranges:
                        r = r.strip()
                        if '-' in r:
                            start, end = map(int, r.split('-'))
                            if start < 1 or end > total_pages:
                                return False, f"页码范围 {r} 超出有效范围 (1-{total_pages})"
                            pages_to_extract.extend(range(start-1, end))
                        else:
                            page = int(r)
                            if page < 1 or page > total_pages:
                                return False, f"页码 {page} 超出有效范围 (1-{total_pages})"
                            pages_to_extract.append(page-1)
                    
                    # 创建新的PDF文件
                    with pikepdf.Pdf.new() as new_pdf:
                        for page_num in pages_to_extract:
                            new_pdf.pages.append(pdf.pages[page_num])
                        output_path = os.path.join(output_dir, f"group_{i+1}.pdf")
                        new_pdf.save(output_path)
                
                return True, f"已成功分割为{len(page_groups)}个文件"
                
        except ValueError as ve:
            return False, f"页码格式错误：{str(ve)}"
        except Exception as e:
            return False, f"分割失败：{str(e)}" 

    @staticmethod
    def merge_pdfs(input_paths, output_path):
        """
        合并多个PDF文件
        :param input_paths: 输入PDF文件路径列表
        :param output_path: 输出PDF文件路径
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 检查输入文件是否都存在
            for path in input_paths:
                if not os.path.exists(path):
                    return False, f"输入文件不存在: {path}"
            
            # 创建输出目录（如果不存在）
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 创建新的PDF文件
            output = pikepdf.Pdf.new()
            
            # 逐个处理输入文件
            for input_path in input_paths:
                try:
                    # 打开PDF文件
                    with pikepdf.Pdf.open(input_path) as pdf:
                        # 复制所有页面
                        for page in pdf.pages:
                            output.pages.append(page)
                except Exception as e:
                    return False, f"处理文件 {input_path} 时出错: {str(e)}"
            
            # 保存合并后的文件
            output.save(output_path,
                    compress_streams=True,
                    preserve_pdfa=True,
                    object_stream_mode=pikepdf.ObjectStreamMode.generate)
            
            return True, f"合并完成，共处理{len(input_paths)}个文件"
            
        except Exception as e:
            return False, f"合并失败: {str(e)}" 

    @staticmethod
    def reorder_pages(input_path, output_path, page_order):
        """
        重新排序PDF页面
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :param page_order: 页面顺序，格式如"3,1,2,4"或"1-2,4,3"
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                return False, "输入文件不存在"
            
            # 创建输出目录（如果不存在）
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 打开PDF文件
            with pikepdf.Pdf.open(input_path) as pdf:
                total_pages = len(pdf.pages)
                
                # 解析页面顺序
                page_numbers = []
                for part in page_order.split(','):
                    if '-' in part:
                        start, end = map(int, part.strip().split('-'))
                        page_numbers.extend(range(start, end + 1))
                    else:
                        page_numbers.append(int(part.strip()))
                
                # 验证页面范围
                for page_num in page_numbers:
                    if page_num < 1 or page_num > total_pages:
                        return False, f"页面编号无效: {page_num}"
                
                # 创建新的PDF文件
                output = pikepdf.Pdf.new()
                
                # 按指定顺序复制页面
                for page_num in page_numbers:
                    output.pages.append(pdf.pages[page_num - 1])
                
                # 保��文件
                output.save(output_path,
                        compress_streams=True,
                        preserve_pdfa=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate)
                
                return True, f"重排序完成，共处理{len(page_numbers)}页"
            
        except Exception as e:
            return False, f"重排序失败: {str(e)}" 

    @staticmethod
    def load_pdf(input_path):
        """
        加载PDF文件
        :param input_path: 输入PDF文件路径
        :return: PDF对象
        """
        try:
            # 先尝试使用 pikepdf 打开
            try:
                return pikepdf.Pdf.open(input_path, allow_overwriting_input=True)
            except pikepdf.PasswordError:
                # 如果文件有密码保护，尝试使用 PyPDF2
                pdf_file = open(input_path, 'rb')
                reader = PdfReader(pdf_file)
                if reader.is_encrypted:
                    # 如果是加密的PDF，尝试使用空密码
                    try:
                        reader.decrypt('')
                    except:
                        pdf_file.close()
                        raise Exception("PDF文件受密码保护")
                return reader
        except Exception as e:
            raise Exception(f"加载PDF失败: {str(e)}") 

    @staticmethod
    def add_page_numbers(input_path, output_path, start_number=1, position='bottom'):
        """
        为PDF添加页码
        :param input_path: 输入PDF文件路径
        :param output_path: 输出PDF文件路径
        :param start_number: 起始页码
        :param position: 页码位置 ('top' 或 'bottom')
        :return: (bool, str) - (是否成功, 错误信息)
        """
        try:
            # 读取原始PDF
            reader = PdfReader(input_path)
            writer = PdfWriter()
            
            # 获取页面尺寸（使用第一页的尺寸）
            if not reader.pages:
                return False, "PDF文件没有页面"
            
            first_page = reader.pages[0]
            mediabox = first_page.mediabox
            page_width = float(mediabox.width)
            page_height = float(mediabox.height)
            
            # 为每一页添加页码
            for i, page in enumerate(reader.pages):
                # 创建页码水印
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=(page_width, page_height))
                c.setFont(PDFEditor.DEFAULT_FONT, 10)  # 使用10号字体
                
                # 计算页码位置
                page_number = str(start_number + i)
                if position == 'bottom':
                    y = 20  # 距底部20点
                else:
                    y = page_height - 20  # 距顶部20点
                
                # 绘制页码
                c.drawCentredString(page_width/2, y, page_number)
                c.save()
                
                # 创建页码水印页
                packet.seek(0)
                number_pdf = PdfReader(packet)
                watermark_page = number_pdf.pages[0]
                
                # 合并页码到原页面
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # 保存结果
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True, f"已成功添加页码，共处理{len(reader.pages)}页"
            
        except Exception as e:
            return False, f"添加页码失败: {str(e)}" 