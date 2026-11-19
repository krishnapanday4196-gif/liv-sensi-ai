# HepatoVision AI
### Deep Learning for Early Detection of Liver Disease Using Imaging

A production-grade Clinical Radiology and Diagnostic Decision Support Web Platform designed for early detection of liver diseases using **Deep Learning (DenseNet-121)**, **Explainable AI (Grad-CAM)**, and **Automated Medical PDF Reporting**.

---

## 🌟 Key Features

1. **Pure HTML5, Modern CSS3 & Vanilla JavaScript Frontend**:
   - Zero complex build steps, fast loading, responsive medical UI (dark/clinical theme).
   - Interactive Radiology Image Viewer with **real-time Grad-CAM Heatmap Blend Slider**.
   - Inverted contrast mode for radiological negative viewing.
   - 1-Click Quick Demonstration presets for instant evaluation (Normal, Fatty Liver, Cirrhosis, Tumor).

2. **Explainable AI (Grad-CAM) Visual Explanations**:
   - Computes activation gradients from the final convolutional layer of DenseNet-121.
   - Highlights the exact spatial Region of Interest (ROI) (nodules, diffuse steatosis, or tumors) in thermal colormap (JET).

3. **Multi-Class Disease Classification**:
   - **Normal Liver**: Healthy baseline parenchyma.
   - **Fatty Liver (Hepatic Steatosis)**: Early reversible metabolic accumulation.
   - **Liver Cirrhosis**: Severe parenchymal coarsening and surface nodularity.
   - **Liver Tumor / HCC**: Focal hypervascular mass lesion.

4. **Automated Clinical PDF Lab Reports**:
   - Instant download of official, print-ready radiology lab reports with patient metadata, embedded scans + heatmaps, AI findings, and doctor signature section.

5. **Patient Audit Trail & History**:
   - Persistent SQLite database logging past scans, clinical parameters, and radiologist review status.

---

## 🚀 How to Run the Website

### Step 1: Start the Backend Server
In your terminal, navigate to the project directory and run:

```bash
python main.py
```

Or using `uvicorn`:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Step 2: Open in Your Browser
Open your web browser and go to:
```
http://127.0.0.1:8000
```

---

## 📁 Project Structure

```
projct/
├── backend/
│   ├── database.py         # SQLite database models & SQLAlchemy ORM
│   ├── model_engine.py     # PyTorch DenseNet-121 & Grad-CAM pipeline
│   ├── report_generator.py # ReportLab medical PDF report generator
│   └── sample_data.py      # Generates synthetic demonstration scans
├── sample_scans/           # Pre-loaded sample medical scans
├── static/
│   ├── css/
│   │   └── style.css       # Pure CSS3 clinical styling & responsive design
│   ├── js/
│   │   └── app.js          # Pure Vanilla JavaScript frontend logic
│   └── index.html          # Main radiology portal webpage
├── uploads/                # User uploaded scans and generated heatmaps
├── reports/                # Generated PDF medical reports
├── main.py                 # FastAPI backend server
└── requirements.txt        # Python package dependencies
```

---

## 🔬 Deep Learning & Clinical Architecture

- **Backbone**: DenseNet-121 (Densely Connected Convolutional Networks).
- **Explainability**: Grad-CAM (Gradient-weighted Class Activation Mapping).
- **Backend API**: FastAPI (Asynchronous high-speed REST endpoints).
- **Database**: SQLite3 via SQLAlchemy ORM.
- **Reporting Engine**: ReportLab Toolkit.
