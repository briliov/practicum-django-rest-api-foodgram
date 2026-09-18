"""Utils for API Foodgram."""

import io
from backend.core.settings import BASE_DIR

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

FONT_PATH = BASE_DIR / 'api' / 'data' / 'fonts' / 'DejaVuSans.ttf'
pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))


def generate_shopping_cart_pdf(ingredients: list) -> io.BytesIO:
    """Generate a PDF document containing a list of shopping cart ingredients.

    Args:
        ingredients (list): A list of dictionaries, where each dict contains
                            the ingredient name, measurement unit, and
                            the summarized total amount.

    Returns:
        io.BytesIO: An in-memory byte buffer containing the generated PDF data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=24,
        leading=28,
        textColor=HexColor('#333333'),
        spaceAfter=25
    )
    item_style = ParagraphStyle(
        'CustomItem',
        parent=styles['Normal'],
        fontName='DejaVuSans',
        fontSize=13,
        leading=20,
        textColor=HexColor('#444444'),
        leftIndent=15,
        spaceAfter=8
    )

    # Build the flowable elements list for the document
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
