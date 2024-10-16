from io import BytesIO
from typing import Tuple

import numpy as np
from pdf2image import convert_from_path
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def draw_centered_image(
    canvas: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    image: ImageReader,
):
    bottom_left_x = x - width / 2
    bottom_left_y = y - height / 2
    canvas.drawImage(
        image,
        bottom_left_x,
        bottom_left_y,
        width=width,
        height=height,
        mask="auto",
    )


def change_base(x: float, y: float, rotation_matrix: np.ndarray) -> Tuple[float, float]:
    # Since we rotated the original coordinates system, use the inverse of the rotation matrix
    # (which is the transposed matrix) to get the coordinates we have to draw at
    new_coordinates = np.transpose(rotation_matrix) @ np.array([[x], [y]])
    return new_coordinates[0, 0], new_coordinates[1, 0]


def fit_image(image_width, image_height, max_image_width, max_image_height, scale):
    if image_width > max_image_width:
        change_ratio = max_image_width / image_width
        image_width = max_image_width
        image_height *= change_ratio
    if image_height > max_image_height:
        change_ratio = max_image_height / image_height
        image_height = max_image_height
        image_width *= change_ratio

    image_width *= scale
    image_height *= scale

    return image_width, image_height


def convert_content_to_images(
    file_name: str, page_width: int, page_height: int, dpi: int
):

    images = convert_from_path(file_name, dpi=dpi, fmt="png", transparent=True)
    pdf = canvas.Canvas(file_name, pagesize=(page_width, page_height))

    for image in images:
        compressed = BytesIO()
        image.save(compressed, format="png", optimize=True, quality=dpi // 10)

        pdf.drawImage(
            ImageReader(compressed),
            0,
            0,
            width=page_width,
            height=page_height,
            mask="auto",
        )
        pdf.showPage()

    pdf.save()
