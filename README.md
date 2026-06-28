# 📄 Resume QR Stamper

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_svg.svg)](https://resumeqrstamper.streamlit.app/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A clean, lightweight Python + Streamlit web tool that stamps a scannable, customized QR code onto an existing resume PDF without altering the underlying layout or font vectors.

🔗 **Live Deployment:** [resumeqrstamper.streamlit.app](https://resumeqrstamper.streamlit.app/)

---

## ✨ Features

- **Live QR Code Preview:** Generates and shows your QR code instantly as you type and change colors.
- **PDF Placement Visualizer:** Renders the first page of your PDF with a bounding box showing exactly where the QR will land.
- **URL Reachability Check:** Lightweight ping checking if your link is active to avoid sending recruiters dead links.
- **Advanced Styling & Customization:**
  - **Color Picker:** Match the QR code to your resume's accent color.
  - **Logo Embedding:** Upload a PNG to sit centered in the QR code (automatically pads & resizes).
  - **Transparency Support:** Enable transparent backgrounds so it merges cleanly over shaded layout elements.
- **UTM Tracking Parameter Builder:** Easily append tracking tags (`utm_source`, `utm_medium`, `utm_campaign`) to monitor recruiter scan rates using Google Analytics or other platforms.
- **Batch Processing:** Drop multiple PDF variants (e.g. customized for different applications), stamp them all simultaneously, and download a packaged `.zip` file.
- **Precise Alignment & Controls:**
  - Standard edge corner selectors (`bottom-right`, `bottom-left`, `top-right`, `top-left`).
  - Size & edge margin sliders.
  - Pixel-perfect horizontal and vertical nudging.
  - Page range selectors (First Page, Last Page, or All Pages).

---

## 🛠️ Installation & Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Vikas-u-rao/resume-qr-stamper.git
cd resume-qr-stamper
```

### 2. Install System Dependencies (Poppler)

The **Placement Visualizer** requires `poppler` to render PDF pages into preview images. Follow the setup for your OS:

- **macOS:**
  ```bash
  brew install poppler
  ```
- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install poppler-utils
  ```
- **Windows:**
  1. Download the latest binary from [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases).
  2. Extract the archive and add the `bin` directory to your system's `PATH` Environment Variable.

### 3. Install Python requirements

It is recommended to run this inside a virtual environment:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Run the Streamlit app

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```text
resume-qr-stamper/
├── app.py                  # Streamlit frontend & UI logic
├── qr_stamper.py           # QR generation, overlay blending, & PDF stamping
├── requirements.txt        # Python dependency definitions
├── .gitignore              # Ignored builds/pycache/temporary PDFs
└── README.md               # User documentation & installation guide
```

---

## 🔒 Security & Privacy

Your privacy is important. All PDF files, URLs, and logos are processed entirely **in system memory only**. No files are saved to server disks, cached, or transmitted to external databases.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
