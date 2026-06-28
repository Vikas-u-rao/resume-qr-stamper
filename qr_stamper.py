import io
import qrcode
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

def generate_qr_image(
    url: str,
    fill_color: str = "black",
    size_px: int = 200,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    transparent_bg: bool = False
) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_correction,
        box_size=4,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    if transparent_bg:
        img = qr.make_image(fill_color=fill_color, back_color="transparent").convert("RGBA")
    else:
        img = qr.make_image(fill_color=fill_color, back_color="white").convert("RGB")

    return img.resize((size_px, size_px), Image.LANCZOS)

def embed_logo_in_qr(qr_img: Image.Image, logo_bytes: bytes) -> Image.Image:
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    qr_w, qr_h = qr_img.size
    logo_size = int(qr_w * 0.20)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
    padding = 4
    bg = Image.new("RGB", (logo_size + padding * 2, logo_size + padding * 2), "white")
    qr_img = qr_img.convert("RGBA")
    qr_img.paste(bg, (pos[0] - padding, pos[1] - padding))
    qr_img.paste(logo, pos, mask=logo.split()[3])
    return qr_img

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
    transparent_bg: bool = False,
    logo_bytes: bytes = None,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    qr_img = generate_qr_image(
        url,
        fill_color=qr_color,
        size_px=200,
        error_correction=error_correction,
        transparent_bg=transparent_bg
    )

    if logo_bytes:
        qr_img = embed_logo_in_qr(qr_img, logo_bytes)

    # Base positioning (ReportLab origin: bottom-left)
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

    # Save PIL image to buffer for ReportLab
    img_buf = io.BytesIO()
    qr_img.save(img_buf, format="PNG")
    img_buf.seek(0)

    c.drawImage(ImageReader(img_buf), x, y, width=qr_size_pt, height=qr_size_pt, mask="auto")

    if label:
        c.setFont("Helvetica", 5)
        c.setFillColor(HexColor(qr_color))
        label_text = "Scan to view"
        text_width = c.stringWidth(label_text, "Helvetica", 5)
        label_x = x + (qr_size_pt - text_width) / 2
        label_y = (y - 7) if "bottom" in position else (y + qr_size_pt + 3)
        c.drawString(label_x, label_y, label_text)

    c.save()
    buf.seek(0)
    return buf.read()

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
    transparent_bg: bool = False,
    logo_bytes: bytes = None,
) -> bytes:
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

        box = page.cropbox if page.cropbox else page.mediabox
        page_width = float(box.width)
        page_height = float(box.height)

        # Correct API: use page.rotation, not page.get("/Rotate", 0)
        rotation = page.rotation
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
            transparent_bg=transparent_bg,
            logo_bytes=logo_bytes,
        )

        overlay_page = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    output_buf = io.BytesIO()
    writer.write(output_buf)
    output_buf.seek(0)
    return output_buf.read()
