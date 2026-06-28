"""
app.py — Streamlit UI for Resume QR Stamper (Phase 1: Core).

Phase 1 features:
  - Upload a single resume PDF
  - Enter a URL to embed
  - Choose corner position, QR size, edge margin, QR color
  - Choose which page(s) to stamp
  - Fine-tune X/Y nudge offsets
  - Download the stamped PDF
"""

import io
import qrcode
import streamlit as st
from qr_stamper import stamp_qr_on_pdf, is_valid_url

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Resume QR Stamper",
    page_icon="📄",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("📄 Resume QR Stamper")
st.markdown(
    "Upload your resume PDF and add a scannable QR code — "
    "no layout damage, just a clean overlay stamp."
)
st.divider()

# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
uploaded_file = st.file_uploader("Upload your Resume PDF", type=["pdf"])

# ---------------------------------------------------------------------------
# URL input
# ---------------------------------------------------------------------------
url = st.text_input(
    "Link to embed in QR",
    placeholder="https://linkedin.com/in/username  or  https://yourportfolio.com",
)

url_valid = is_valid_url(url) if url else False
if url and not url_valid:
    st.error("Invalid URL — must start with http:// or https:// and have a valid domain.")

st.divider()

# ---------------------------------------------------------------------------
# QR settings
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    position = st.selectbox(
        "QR Corner Position",
        options=["bottom-right", "bottom-left", "top-right", "top-left"],
        index=0,
    )
with col2:
    qr_color = st.color_picker("QR Color", value="#000000")

col3, col4 = st.columns(2)
with col3:
    qr_size = st.slider(
        "QR Size (Points)",
        min_value=40,
        max_value=100,
        value=60,
        step=5,
        help="60 pt ≈ 2.1 cm on the printed page.",
    )
with col4:
    margin_pt = st.slider(
        "Edge Margin (Points)",
        min_value=5,
        max_value=40,
        value=18,
        step=1,
        help="Distance from QR to nearest page edge. 18 pt ≈ 6.35 mm.",
    )

col5, col6 = st.columns(2)
with col5:
    pages_option = st.radio(
        "Apply QR To",
        options=["First page only", "Last page only", "All pages"],
        index=0,
    )
    pages_map = {
        "First page only": "first",
        "Last page only": "last",
        "All pages": "all",
    }
    pages = pages_map[pages_option]

with col6:
    show_label = st.checkbox("Show 'Scan to view' label", value=True)

# Fine-tune nudge controls
with st.expander("⚙️ Fine-Tune Position (Nudge)"):
    st.caption("Use these if the QR overlaps elements in your resume layout.")
    adj1, adj2 = st.columns(2)
    with adj1:
        offset_x = st.slider("Horizontal Nudge (pt)", min_value=-50, max_value=50, value=0)
    with adj2:
        offset_y = st.slider("Vertical Nudge (pt)", min_value=-50, max_value=50, value=0)

st.divider()

# ---------------------------------------------------------------------------
# Stamp button
# ---------------------------------------------------------------------------
if st.button("🔖 Stamp QR onto Resume", use_container_width=True, type="primary"):
    if not uploaded_file:
        st.error("Please upload a resume PDF first.")
    elif not url_valid:
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Stamping QR onto your resume…"):
            output_bytes = stamp_qr_on_pdf(
                input_pdf_bytes=uploaded_file.getvalue(),
                url=url,
                position=position,
                qr_size_pt=float(qr_size),
                margin_pt=float(margin_pt),
                label=show_label,
                pages=pages,
                qr_color=qr_color,
                offset_x=float(offset_x),
                offset_y=float(offset_y),
            )

        st.success("Done! Download your stamped resume below.")
        st.download_button(
            label="⬇️ Download Stamped Resume",
            data=output_bytes,
            file_name="resume_with_qr.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

st.divider()
st.caption(
    "Your file is processed in memory only and is never written to disk or stored on any server."
)
