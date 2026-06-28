"""
qr_stamper.py — Core logic for Resume QR Stamper.
Handles QR generation, PDF overlay creation, and PDF stamping.
All known bug fixes applied (PIL drawImage, page.rotation, HexColor, URL validation).
"""

import io
import qrcode
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

def is_valid_url(url: str) -> bool:
    """Validate URL using urllib.parse — accepts only http/https with a real netloc."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


# ---------------------------------------------------------------------------
# QR image generation
# ---------------------------------------------------------------------------

def generate_qr_image(
    url: str,
    fill_color: str = "black",
    size_px: int = 200,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
) -> Image.Image:
    """
    Generate a QR code PIL Image for the given URL.

    Args:
        url: The URL to encode.
        fill_color: Hex string or named color for the dark modules.
        size_px: Output image size in pixels (square).
        error_correction: qrcode error correction constant.

    Returns:
        PIL Image in RGB mode.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_correction,
        box_size=4,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color="white").convert("RGB")
    return img.resize((size_px, size_px), Image.LANCZOS)


# ---------------------------------------------------------------------------
# ReportLab overlay PDF creation
# ---------------------------------------------------------------------------

def create_qr_overlay_pdf(
    url: str,
    page_width: float,
    page_height: float,
    position: str = "bottom-right",
    qr_size_pt: float = 60,
    margin_pt: float = 18,
    label: bool = True,
    qr_color: str = "#000000",
    offset_x: float = 0,
    offset_y: float = 0,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
) -> bytes:
    """
    Create a single-page transparent PDF with only the QR stamp.
    This overlay is later merged onto the original resume page.

    Args:
        url: URL to encode in the QR.
        page_width: Width of the target PDF page in points.
        page_height: Height of the target PDF page in points.
        position: Corner placement — 'bottom-right', 'bottom-left', 'top-right', 'top-left'.
        qr_size_pt: QR code size in PDF points.
        margin_pt: Gap between QR edge and page edge, in points.
        label: If True, draw a small "Scan to view" caption near the QR.
        qr_color: Hex color string for the QR modules.
        offset_x: Horizontal nudge in points (positive = right).
        offset_y: Vertical nudge in points (positive = up in PDF coords).
        error_correction: qrcode error correction constant.

    Returns:
        PDF bytes of the overlay page.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    # Generate QR image
    qr_img = generate_qr_image(
        url,
        fill_color=qr_color,
        size_px=200,
        error_correction=error_correction,
    )

    # Fix: save PIL image to BytesIO buffer before passing to ReportLab.
    # drawInlineImage / drawImage do NOT accept PIL Image objects directly.
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # Compute position (ReportLab origin is bottom-left of page)
    if position == "bottom-right":
        x = page_width - qr_size_pt - margin_pt
        y = margin_pt
    elif position == "bottom-left":
        x = margin_pt
        y = margin_pt
    elif position == "top-right":
        x = page_width - qr_size_pt - margin_pt
        y = page_height - qr_size_pt - margin_pt
    elif position == "top-left":
        x = margin_pt
        y = page_height - qr_size_pt - margin_pt
    else:
        x = page_width - qr_size_pt - margin_pt
        y = margin_pt

    x += offset_x
    y += offset_y

    # Draw QR onto canvas
    c.drawImage(ImageReader(img_buf), x, y, width=qr_size_pt, height=qr_size_pt, mask="auto")

    # Optional label
    if label:
        c.setFont("Helvetica", 5)
        # Fix: setFillColor does not accept raw hex strings — use HexColor().
        c.setFillColor(HexColor(qr_color))
        label_text = "Scan to view"
        text_width = c.stringWidth(label_text, "Helvetica", 5)
        label_x = x + (qr_size_pt - text_width) / 2
        label_y = (y - 7) if "bottom" in position else (y + qr_size_pt + 3)
        c.drawString(label_x, label_y, label_text)

    c.save()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Main stamp function
# ---------------------------------------------------------------------------

def stamp_qr_on_pdf(
    input_pdf_bytes: bytes,
    url: str,
    position: str = "bottom-right",
    qr_size_pt: float = 60,
    margin_pt: float = 18,
    label: bool = True,
    pages: str = "first",
    qr_color: str = "#000000",
    offset_x: float = 0,
    offset_y: float = 0,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
) -> bytes:
    """
    Stamp a QR code overlay onto a PDF and return the resulting PDF bytes.

    Args:
        input_pdf_bytes: Raw bytes of the source PDF.
        url: URL to embed in the QR code.
        position: Corner placement — 'bottom-right', 'bottom-left', 'top-right', 'top-left'.
        qr_size_pt: QR code size in PDF points (1 pt = 1/72 inch).
        margin_pt: Edge margin in points.
        label: Whether to print a "Scan to view" caption.
        pages: Which pages to stamp — 'first', 'last', or 'all'.
        qr_color: Hex color for QR modules (e.g. "#000000").
        offset_x: Fine-tune horizontal position in points.
        offset_y: Fine-tune vertical position in points.
        error_correction: qrcode error correction constant.

    Returns:
        PDF bytes with QR overlay merged.
    """
    reader = PdfReader(io.BytesIO(input_pdf_bytes))
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):
        is_target = (
            pages == "all"
            or (pages == "first" and i == 0)
            or (pages == "last" and i == total_pages - 1)
        )

        if not is_target:
            writer.add_page(page)
            continue

        # Use cropbox if available, else mediabox
        box = page.cropbox if page.cropbox else page.mediabox
        page_width = float(box.width)
        page_height = float(box.height)

        # Fix: use page.rotation property instead of page.get("/Rotate", 0)
        rotation = page.rotation  # returns 0 if not set
        if rotation in [90, 270]:
            page_width, page_height = page_height, page_width

        overlay_bytes = create_qr_overlay_pdf(
            url=url,
            page_width=page_width,
            page_height=page_height,
            position=position,
            qr_size_pt=qr_size_pt,
            margin_pt=margin_pt,
            label=label,
            qr_color=qr_color,
            offset_x=offset_x,
            offset_y=offset_y,
            error_correction=error_correction,
        )

        overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    output_buf = io.BytesIO()
    writer.write(output_buf)
    output_buf.seek(0)
    return output_buf.read()
