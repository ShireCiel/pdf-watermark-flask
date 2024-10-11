import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from flask import Flask, render_template, request, send_file
import os
from tempfile import NamedTemporaryFile
from typing import Union
import datetime
import threading
import time

import pypdf

from draw import draw_watermarks

from pdf_watermark.options import Alignments, DrawingOptions, GridOptions, InsertOptions
from utils import convert_content_to_images

# 注册字体
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('Alibaba_PuHuiTi_2.0_55_Regular_55_Regular', './font/Alibaba_PuHuiTi_2.0_55_Regular_55_Regular.ttf'))

# ... 然后在使用字体的地方 ...
new_font="Alibaba_PuHuiTi_2.0_55_Regular_55_Regular"


class AddPdfWatermark:
    def __init__(self, file_path: str, add_text: str):
        self.file_path = file_path
        self.add_text = add_text
        self.init_draw_option()

    def init_draw_option(self):
        self.myDrawOption = DrawingOptions(
            watermark=self.add_text + ":Certified Use " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            opacity=0.25,
            angle=30,
            text_color="#9c9c9c",
            text_font=new_font,
            text_size=15,
            unselectable=False,
            image_scale=False,
            save_as_image=False,
            dpi=300
        )
        self.myGridOptions = GridOptions(
            horizontal_boxes=3,
            vertical_boxes=4,
            margin=False
        )


    def add_pdf_watermark(self):
        output = self.file_path + ".output"
        pdf_to_transform = pypdf.PdfReader(self.file_path)
        pdf_box = pdf_to_transform.pages[0].mediabox
        page_width = pdf_box.width
        page_height = pdf_box.height
        with NamedTemporaryFile(delete=False) as temporary_file:
        # The watermark is stored in a temporary pdf file
            draw_watermarks(
                temporary_file.name,
                page_width,
                page_height,
                self.myDrawOption,
                self.myGridOptions,
        )

        if self.myDrawOption.unselectable and not self.myDrawOption.save_as_image:
            convert_content_to_images(
                temporary_file.name, page_width, page_height, self.myDrawOption.dpi
            )

        watermark_pdf = pypdf.PdfReader(temporary_file.name)
        pdf_writer = pypdf.PdfWriter()

        for page in pdf_to_transform.pages:
            page.merge_page(watermark_pdf.pages[0])
            pdf_writer.add_page(page)

        # Remove temp file - https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file
        temporary_file.close()
        os.unlink(temporary_file.name)
        # 保存输出文件
        with open(output, "wb") as f:
            pdf_writer.write(f)
        # 保存图片
        if self.myDrawOption.save_as_image:
            convert_content_to_images(output, page_width, page_height, self.myDrawOption.dpi)
        return

def delayed_file_deletion(file_path, delay=60):
    time.sleep(delay)
    try:
        os.remove(file_path)
        print(f"文件 {file_path} 已被删除")
    except Exception as e:
        print(f"删除文件 {file_path} 时出错: {e}")

import ipdb

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/upload', methods=["POST"])
def upload():
    file = request.files['file']
    if file:
        filename = file.filename
        file_name_list = filename.split('.')
        file_name, file_extension = file_name_list[:-1], file_name_list[-1]
        file_path = 'uploads/' + filename + file_extension
        output_path = file_path + ".output"
        file.save(file_path)
        add_text = request.form.get('add_text')

        add_pdf_watermark = AddPdfWatermark(file_path, add_text)
        add_pdf_watermark.add_pdf_watermark()
        os.remove(file_path)
        
        # 创建一个新线程来处理延迟删除
        threading.Thread(target=delayed_file_deletion, args=(output_path,)).start()
        
        new_filename = f"{file_name}_{add_text}.{file_extension}"
        return send_file(output_path, as_attachment=True, download_name=new_filename)
    else:
        return "文件上传失败"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")