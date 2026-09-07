"""Utils for API Foodgram."""

from django.core.files.base import ContentFile
from rest_framework import serializers
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import base64
import uuid


class Base64ImageField(serializers.ImageField):
    """Custom field for decode images from Base64 format"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            cleaned_data = data.replace(' ', '')
            format, imgstr = cleaned_data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(base64.b64decode(imgstr), name=f'{id}.{ext}')
        return super().to_internal_value(data)


def generate_shopping_cart_pdf(ingredients: list) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=24,
        leading=28,
        textColor='#333333',
        spaceAfter=25
    )
    item_style = ParagraphStyle(
        'CustomItem',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=13,
        leading=20,
        textColor='#444444',
        leftIndent=15,
        spaceAfter=8
    )

    story = [Paragraph("Список покупок", title_style), Spacer(1, 10)]

    for ingredient in ingredients:
        name = ingredient['ingredients__name']
        unit = ingredient['ingredients__measurement_unit']
        amount = ingredient['total_amount']
        text = f"• &nbsp; {name} ({unit}) &mdash; {amount}"
        story.append(Paragraph(text, item_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
