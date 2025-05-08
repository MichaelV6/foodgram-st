from PIL import Image, ImageOps
from django.utils.html import format_html

from foodgram.constants import MAX_WIDTH_SIZE, MAX_HEIGHT_SIZE, SCALE_QUALITY


def image_compress(image_path):
    """Оптимизация изображений"""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    if img.height > MAX_HEIGHT_SIZE or img.width > MAX_WIDTH_SIZE:
        output_size = (MAX_HEIGHT_SIZE, MAX_WIDTH_SIZE)
        img.thumbnail(output_size)
    img = ImageOps.exif_transpose(img)
    img.save(image_path, format='JPEG', quality=SCALE_QUALITY, optimize=True)


def admin_thumbnail(image_field, width=50, height=50, rounded=True):
    """Генерирует HTML для отображения миниатюры изображения в админке"""
    if image_field:
        style = ""
        if rounded:
            style = "style='object-fit: cover; border-radius: 50%;'"
        return format_html(
            f'<img src="{{}}" width="{width}" height="{height}" {style} />',
            image_field.url
        )
    return "Нет изображения"
