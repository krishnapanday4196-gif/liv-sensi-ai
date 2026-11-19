import os
import shutil
import uuid
import json
import socket
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import qrcode

from backend.database import init_db, get_db, PatientRecord
from backend.model_engine import diagnostic_engine
from backend.report_generator import generate_pdf_report
from backend.sample_data import generate_synthetic_samples

# Initialize app and database
init_db()
generate_synthetic_samples()

app = FastAPI(
    title="HepatoVision AI - Liver Disease Detection API",
    description="Clinical Deep Learning Radiology Portal for Liver Disease Early Detection",
    version="2.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SAMPLES_DIR = os.path.join(BASE_DIR, "sample_scans")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def get_local_ip():
    """Detects primary local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def generate_network_qr():
    """Generates a QR code pointing to the LAN mobile URL."""
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:8000"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    qr_path = os.path.join(STATIC_DIR, "mobile_qr.png")
    img.save(qr_path)
    return local_ip, mobile_url

LOCAL_IP, MOBILE_URL = generate_network_qr()

# Mount static file directories
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount("/sample_scans", StaticFiles(directory=SAMPLES_DIR), name="sample_scans")


@app.get("/")
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/network-info")
def get_network_info():
    """Returns dynamic local LAN IP, mobile access link, and QR code path."""
    current_ip = get_local_ip()
    current_url = f"http://{current_ip}:8000"
    return JSONResponse(content={
        "local_ip": current_ip,
        "port": 8000,
        "mobile_url": current_url,
        "qr_code_url": "/static/mobile_qr.png"
    })


@app.get("/api/samples")
def get_sample_scans():
    """Returns available demonstration scans."""
    samples = [
        {
            "id": "sample_normal_liver.png",
            "name": "Normal Healthy Liver",
            "type": "Ultrasound / CT Baseline",
            "description": "Uniform parenchymal echotexture with smooth margins & clear portal branches.",
            "url": "/sample_scans/sample_normal_liver.png",
            "typical_patient": {"name": "Suresh Patel", "age": 34, "gender": "Male", "symptoms": "Routine Health Screening", "alt_ast": "ALT: 22 U/L, AST: 20 U/L"}
        },
        {
            "id": "sample_fatty_liver.png",
            "name": "Fatty Liver (Steatosis)",
            "type": "Early Stage Metabolic Liver Disease",
            "description": "Hyper-reflective echogenic parenchyma with characteristic acoustic beam attenuation.",
            "typical_patient": {"name": "Meera Verma", "age": 48, "gender": "Female", "symptoms": "Mild Fatigue, Right Upper Quadrant Discomfort", "alt_ast": "ALT: 64 U/L, AST: 48 U/L"}
        },
        {
            "id": "sample_cirrhosis_liver.png",
            "name": "Liver Cirrhosis",
            "type": "Chronic Fibrosis & Parenchymal Scarring",
            "description": "Coarse, mottled parenchymal architecture with nodular, irregular capsular surface.",
            "typical_patient": {"name": "Rajesh Kumar", "age": 56, "gender": "Male", "symptoms": "Jaundice, Ascites, Mild Confusion", "alt_ast": "ALT: 110 U/L, AST: 145 U/L"}
        },
        {
            "id": "sample_liver_tumor.png",
            "name": "Liver Tumor / HCC",
            "type": "Focal Hepatic Neoplasm / Carcinoma",
            "description": "Focal mass lesion with peripheral hypervascular rim and heterogeneous internal core.",
            "typical_patient": {"name": "Anil Deshmukh", "age": 62, "gender": "Male", "symptoms": "Unexplained Weight Loss, Persistent Hepatic Pain", "alt_ast": "ALT: 185 U/L, AST: 210 U/L"}
        }
    ]
    return JSONResponse(content=samples)


@app.post("/api/analyze")
async def analyze_scan(
    file: UploadFile = File(None),
    sample_name: str = Form(None),
    patient_name: str = Form("Anonymous"),
    patient_id: str = Form(None),
    age: int = Form(45),
    gender: str = Form("Male"),
    symptoms: str = Form("None Reported"),
    alt_ast: str = Form("Within Normal Limits"),
    db: Session = Depends(get_db)
):
    """
    Receives scan image and clinical parameters, runs Deep Learning inference + Grad-CAM,
    and returns comprehensive medical evaluation.
    """
    if not patient_id:
        patient_id = f"PT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    unique_token = uuid.uuid4().hex[:8]
    scan_filename = f"scan_{unique_token}.png"
    heatmap_filename = f"heatmap_{unique_token}.png"

    scan_path = os.path.join(UPLOADS_DIR, scan_filename)
    heatmap_path = os.path.join(UPLOADS_DIR, heatmap_filename)

    filename_hint = ""
    if sample_name:
        sample_path = os.path.join(SAMPLES_DIR, sample_name)
        if not os.path.exists(sample_path):
            raise HTTPException(status_code=404, detail="Selected sample scan not found.")
        shutil.copy(sample_path, scan_path)
        filename_hint = sample_name
    elif file and file.filename:
        filename_hint = file.filename
        with open(scan_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        raise HTTPException(status_code=400, detail="Please upload a scan image or select a sample scan.")

    # Execute Deep Learning & Grad-CAM pipeline
    ai_result = diagnostic_engine.predict_and_explain(
        image_path=scan_path,
        output_heatmap_path=heatmap_path,
        filename_hint=filename_hint
    )

    # Save to SQLite Database
    record = PatientRecord(
        patient_id=patient_id,
        patient_name=patient_name,
        age=age,
        gender=gender,
        symptoms=symptoms,
        alt_ast=alt_ast,
        scan_filename=scan_filename,
        heatmap_filename=heatmap_filename,
        predicted_class=ai_result["predicted_class"],
        confidence=ai_result["confidence"],
        risk_level=ai_result["risk_level"],
        clinical_findings=ai_result["findings"],
        recommendations=ai_result["recommendations"],
        probabilities=json.dumps(ai_result["probabilities"]),
        doctor_status="Pending Radiologist Review",
        doctor_notes="AI Deep Learning assessment generated. Radiologist correlation pending."
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Pre-generate PDF report
    pdf_filename = f"report_PT_{record.id}_{unique_token}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
    report_data = {
        "patient_id": record.patient_id,
        "patient_name": record.patient_name,
        "age": record.age,
        "gender": record.gender,
        "symptoms": record.symptoms,
        "alt_ast": record.alt_ast,
        "predicted_class": record.predicted_class,
        "confidence": record.confidence,
        "risk_level": record.risk_level,
        "findings": record.clinical_findings,
        "recommendations": record.recommendations,
        "scan_path": scan_path,
        "heatmap_path": heatmap_path,
        "doctor_notes": record.doctor_notes
    }
    generate_pdf_report(report_data, pdf_path)

    return JSONResponse(content={
        "record_id": record.id,
        "patient_id": record.patient_id,
        "patient_name": record.patient_name,
        "predicted_class": record.predicted_class,
        "confidence": record.confidence,
        "risk_level": record.risk_level,
        "badge_color": ai_result["badge_color"],
        "findings": record.clinical_findings,
        "recommendations": record.recommendations,
        "probabilities": ai_result["probabilities"],
        "scan_url": f"/uploads/{scan_filename}",
        "heatmap_url": f"/uploads/{heatmap_filename}",
        "report_url": f"/api/report/{record.id}",
        "doctor_status": record.doctor_status,
        "doctor_notes": record.doctor_notes,
        "created_at": record.created_at.strftime("%d %b %Y, %H:%M")
    })


@app.get("/api/history")
def get_analysis_history(db: Session = Depends(get_db)):
    """Returns past patient diagnostic records."""
    records = db.query(PatientRecord).order_by(PatientRecord.created_at.desc()).limit(50).all()
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "patient_id": r.patient_id,
            "patient_name": r.patient_name,
            "age": r.age,
            "gender": r.gender,
            "symptoms": r.symptoms,
            "predicted_class": r.predicted_class,
            "confidence": r.confidence,
            "risk_level": r.risk_level,
            "scan_url": f"/uploads/{r.scan_filename}",
            "heatmap_url": f"/uploads/{r.heatmap_filename}",
            "doctor_status": r.doctor_status,
            "doctor_notes": r.doctor_notes,
            "created_at": r.created_at.strftime("%d %b %Y, %H:%M")
        })
    return JSONResponse(content=results)


@app.get("/api/report/{record_id}")
def download_patient_report(record_id: int, db: Session = Depends(get_db)):
    """Serves the generated PDF diagnostic report."""
    record = db.query(PatientRecord).filter(PatientRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Diagnostic record not found.")

    pdf_filename = f"report_record_{record_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    scan_path = os.path.join(UPLOADS_DIR, record.scan_filename)
    heatmap_path = os.path.join(UPLOADS_DIR, record.heatmap_filename)

    report_data = {
        "patient_id": record.patient_id,
        "patient_name": record.patient_name,
        "age": record.age,
        "gender": record.gender,
        "symptoms": record.symptoms,
        "alt_ast": record.alt_ast,
        "predicted_class": record.predicted_class,
        "confidence": record.confidence,
        "risk_level": record.risk_level,
        "findings": record.clinical_findings,
        "recommendations": record.recommendations,
        "scan_path": scan_path,
        "heatmap_path": heatmap_path,
        "doctor_notes": record.doctor_notes
    }
    generate_pdf_report(report_data, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"HepatoVision_Report_{record.patient_id}.pdf"
    )


@app.post("/api/verify/{record_id}")
def verify_patient_record(
    record_id: int,
    doctor_status: str = Form(...),
    doctor_notes: str = Form(...),
    db: Session = Depends(get_db)
):
    """Allows doctor/radiologist to confirm or add clinical notes."""
    record = db.query(PatientRecord).filter(PatientRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")

    record.doctor_status = doctor_status
    record.doctor_notes = doctor_notes
    db.commit()

    return JSONResponse(content={"status": "success", "message": "Clinical review updated successfully."})


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*65)
    print("  HEPATOVISION AI - CLINICAL RADIOLOGY PORTAL")
    print(f"  Local PC Access:   http://127.0.0.1:8000")
    print(f"  Mobile LAN Access: http://{LOCAL_IP}:8000")
    print("="*65 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
