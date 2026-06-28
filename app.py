import io
import zipfile
import qrcode
import streamlit as st
import requests
from urllib.parse import urlparse, urlencode, urlunparse
from pdf2image import convert_from_bytes
from PIL import ImageDraw
from qr_stamper import stamp_qr_on_pdf, is_valid_url

st.set_page_config(page_title="Resume QR Stamper", page_icon="📄", layout="centered")

st.title("📄 Resume QR Stamper")
st.markdown(
    "Upload your resume PDF and add a scannable QR code — "
    "no structural layout damage, just a clean overlay stamp."
)
st.divider()

# --- Upload ---
uploaded_files = st.file_uploader(
    "Upload Resume PDF(s)",
    type=["pdf"],
    accept_multiple_files=True
)

# --- URL Input ---
url_raw = st.text_input(
    "Link to embed in QR",
    placeholder="https://linkedin.com/in/username or https://yourportfolio.com",
)

# URL Validation feedback
url_valid = is_valid_url(url_raw) if url_raw else False
if url_raw and not url_valid:
    st.error("URL format is invalid. Must start with http:// or https:// and have a valid domain.")

# URL Reachability Check
if url_valid:
    try:
        r = requests.head(url_raw, timeout=5, allow_redirects=True)
        if r.status_code < 400:
            st.success(f"✅ URL reachable (HTTP {r.status_code})")
        else:
            st.warning(f"⚠️ URL returned HTTP {r.status_code} — double-check before embedding.")
    except requests.exceptions.ConnectionError:
        st.error("❌ URL unreachable — could not connect.")
    except requests.exceptions.Timeout:
        st.warning("⚠️ URL check timed out. Verify it's accessible publicly.")
    except Exception as e:
        st.warning(f"⚠️ Could not verify URL: {e}")

# --- UTM Builder ---
utm_url = url_raw
with st.expander("📊 UTM Tracking Parameters (optional)"):
    st.markdown("<small>Append UTM tags so you can track QR scan traffic in analytics.</small>", unsafe_allow_html=True)
    utm_source   = st.text_input("utm_source",   value="resume",  placeholder="resume")
    utm_medium   = st.text_input("utm_medium",   value="qr_code", placeholder="qr_code")
    utm_campaign = st.text_input("utm_campaign", value="",        placeholder="job_application_2025")

    if url_valid and (utm_source or utm_medium or utm_campaign):
        parsed = urlparse(url_raw)
        params = {}
        if utm_source:   params["utm_source"]   = utm_source
        if utm_medium:   params["utm_medium"]   = utm_medium
        if utm_campaign: params["utm_campaign"] = utm_campaign
        utm_url = urlunparse(parsed._replace(query=urlencode(params)))
        st.code(utm_url, language=None)
        st.caption("This final URL will be embedded in the QR.")

st.divider()

# --- QR Settings ---
col1, col2 = st.columns(2)
with col1:
    position = st.selectbox(
        "QR Target Corner Position",
        options=["bottom-right", "bottom-left", "top-right", "top-left"],
        index=0,
    )
with col2:
    qr_color = st.color_picker("QR Accent Color", value="#000000")

col3, col4 = st.columns(2)
with col3:
    qr_size = st.slider("QR Size (Points)", min_value=40, max_value=100, value=60, step=5,
                        help="60pt ≈ 2.1cm")
with col4:
    margin_pt = st.slider("Edge Margin (Points)", min_value=5, max_value=40, value=18, step=1,
                          help="Distance from QR to page edge. 18pt ≈ 6.35mm")

col5, col6 = st.columns(2)
with col5:
    pages_option = st.radio(
        "Apply QR To",
        options=["First page only", "Last page only", "All pages"],
        index=0,
    )
    pages_map = {"First page only": "first", "Last page only": "last", "All pages": "all"}
    pages = pages_map[pages_option]

with col6:
    ec_option = st.radio(
        "Error Correction Level",
        options=["Low (L) — cleanest", "Medium (M) — recommended", "High (H) — for logo embed"],
        index=1,
        help="Higher = denser QR. Use High only when embedding a logo."
    )
    ec_map = {
        "Low (L) — cleanest": qrcode.constants.ERROR_CORRECT_L,
        "Medium (M) — recommended": qrcode.constants.ERROR_CORRECT_M,
        "High (H) — for logo embed": qrcode.constants.ERROR_CORRECT_H,
    }
    error_correction = ec_map[ec_option]

show_label    = st.checkbox("Show 'Scan to view' label", value=True)
transparent_bg = st.checkbox("Transparent QR background (for colored resume templates)", value=False)

# --- Logo Embed ---
logo_file = st.file_uploader("Embed Logo in QR Center (optional, PNG recommended)", type=["png", "jpg", "jpeg"])
logo_bytes = logo_file.read() if logo_file else None
if logo_file and "High" not in ec_option:
    st.warning("⚠️ Switch Error Correction to High (H) when embedding a logo.")

# --- Fine Tune ---
with st.expander("⚙️ Fine-Tune Positioning (Nudge Coordinates)"):
    st.markdown("<small>Use these if the QR overlaps elements in your resume layout.</small>", unsafe_allow_html=True)
    adj1, adj2 = st.columns(2)
    with adj1:
        offset_x = st.slider("Horizontal Nudge", min_value=-50, max_value=50, value=0)
    with adj2:
        offset_y = st.slider("Vertical Nudge", min_value=-50, max_value=50, value=0)

# --- Live QR Preview ---
if url_valid:
    st.divider()
    st.markdown("**QR Preview**")
    qr = qrcode.QRCode(error_correction=error_correction, box_size=4, border=2)
    qr.add_data(utm_url)
    qr.make(fit=True)
    preview_img = qr.make_image(fill_color=qr_color, back_color="white").convert("RGB")
    buf = io.BytesIO()
    preview_img.save(buf, format="PNG")
    st.image(buf.getvalue(), width=150)

# --- PDF Page Placement Preview ---
if uploaded_files:
    st.divider()
    st.markdown("**Placement Preview** (first uploaded file, first page)")
    try:
        pages_img = convert_from_bytes(uploaded_files[0].getvalue(), first_page=1, last_page=1, dpi=100)
        preview_page = pages_img[0].copy()
        draw = ImageDraw.Draw(preview_page)
        W, H = preview_page.size
        dpi_scale = 100 / 72
        qr_px = int(qr_size * dpi_scale)
        margin_px = int(margin_pt * dpi_scale)
        ox = int(offset_x * dpi_scale)
        oy = int(offset_y * dpi_scale)

        pos_map = {
            "bottom-right": (W - qr_px - margin_px + ox, H - qr_px - margin_px - oy),
            "bottom-left":  (margin_px + ox,              H - qr_px - margin_px - oy),
            "top-right":    (W - qr_px - margin_px + ox, margin_px - oy),
            "top-left":     (margin_px + ox,              margin_px - oy),
        }
        px, py = pos_map[position]
        draw.rectangle([px, py, px + qr_px, py + qr_px], outline=qr_color, width=3)
        st.image(preview_page, caption="QR placement shown as outline box", use_container_width=True)
    except Exception as e:
        st.warning(f"Preview unavailable: {e}. Install poppler to enable this feature.")

st.divider()

# --- Execute ---
if st.button("🔖 Stamp QR onto Resume(s)", use_container_width=True, type="primary"):
    if not uploaded_files:
        st.error("Please upload at least one resume PDF.")
    elif not url_valid:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Stamping document(s)..."):
            if len(uploaded_files) == 1:
                output_bytes = stamp_qr_on_pdf(
                    input_pdf_bytes=uploaded_files[0].getvalue(),
                    url=utm_url,
                    position=position,
                    qr_size_pt=float(qr_size),
                    margin_pt=float(margin_pt),
                    label=show_label,
                    pages=pages,
                    qr_color=qr_color,
                    offset_x=float(offset_x),
                    offset_y=float(offset_y),
                    error_correction=error_correction,
                    transparent_bg=transparent_bg,
                    logo_bytes=logo_bytes,
                )
                st.success("Done! Download your stamped resume below.")
                st.download_button(
                    "⬇️ Download Stamped Resume",
                    data=output_bytes,
                    file_name="resume_with_qr.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f in uploaded_files:
                        stamped = stamp_qr_on_pdf(
                            input_pdf_bytes=f.getvalue(),
                            url=utm_url,
                            position=position,
                            qr_size_pt=float(qr_size),
                            margin_pt=float(margin_pt),
                            label=show_label,
                            pages=pages,
                            qr_color=qr_color,
                            offset_x=float(offset_x),
                            offset_y=float(offset_y),
                            error_correction=error_correction,
                            transparent_bg=transparent_bg,
                            logo_bytes=logo_bytes,
                        )
                        zf.writestr(f"stamped_{f.name}", stamped)
                zip_buf.seek(0)
                st.success(f"Done! {len(uploaded_files)} files stamped.")
                st.download_button(
                    "⬇️ Download All Stamped Resumes (ZIP)",
                    data=zip_buf.getvalue(),
                    file_name="stamped_resumes.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

st.divider()
st.caption("Your file is processed in memory only and is never written to disk or stored on any server.")
