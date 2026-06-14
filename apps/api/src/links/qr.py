from io import BytesIO

import qrcode
from qrcode.image.svg import SvgPathImage


def generate_qr_png(value: str) -> bytes:
    """Generate PNG QR image bytes for value."""
    image = qrcode.make(value)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_svg(value: str) -> bytes:
    """Generate SVG QR image bytes for value."""
    image = qrcode.make(value, image_factory=SvgPathImage)
    buffer = BytesIO()
    image.save(buffer)
    return buffer.getvalue()
