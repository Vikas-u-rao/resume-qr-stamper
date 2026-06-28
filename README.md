# Resume QR Stamper

A lightweight Python + Streamlit tool that stamps a scannable QR code onto a resume PDF without altering the underlying layout.

---

## Project Structure

```
resume-qr-stamper/
├── app.py           # Streamlit UI
├── qr_stamper.py    # Core logic (QR generation, PDF stamping)
├── requirements.txt # Python dependencies
└── README.md
```

---

## Quick Start

### 1. Install system dependency (for PDF preview — optional in Phase 1)

| OS | Command |
|---|---|
| Ubuntu/Debian | `sudo apt install poppler-utils` |
| macOS | `brew install poppler` |
| Windows | Download from [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases) |

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Phase 1 Features (Core)

| Feature | Status |
|---|---|
| Upload a resume PDF | ✅ |
| URL input with format validation | ✅ |
| Corner position selector | ✅ |
| QR size slider | ✅ |
| Edge margin slider | ✅ |
| QR color picker | ✅ |
| Page selector (first / last / all) | ✅ |
| "Scan to view" label toggle | ✅ |
| X/Y nudge offsets | ✅ |
| Download stamped PDF | ✅ |

---

## Planned Features (Phase 2+)

- Live QR preview
- PDF placement visualizer (poppler-based page render)
- URL reachability check
- Error correction level selector
- QR logo/icon embed
- Transparent QR background
- UTM parameter builder
- Multi-file batch + ZIP download
