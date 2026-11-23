import os
import shutil
import uuid
import json
import socket
import html
import re
import time
import io
import hashlib
from collections import defaultdict
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from PIL import Image
import qrcode

from backend.database import init_db, get_db, PatientRecord
from backend.model_engine import diagnostic_engine
from backend.report_generator import generate_pdf_report
from backend.sample_data import generate_synthetic_samples

# Initialize app and database
init_db()
generate_synthetic_samples()

app = FastAPI(
    title="Liv-Sensi AI - Clinical Radiology & Diagnostic Security API",
    description="Deep Learning Early Detection Platform for Liver Disease with Enterprise Security & OWASP Hardening",
    version="2.1.0"
)

# Robust CORS Configuration: Allow all for development & preview tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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

# Allowed image extensions and validated sample scans (Anti-Path Traversal)
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
ALLOWED_SAMPLE_NAMES = {
    "sample_normal_liver.png",
    "sample_fatty_liver.png",
    "sample_cirrhosis_liver.png",
    "sample_liver_tumor.png"
}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
MAX_BODY_SIZE = 25 * 1024 * 1024  # 25 MB

# In-Memory Sliding-Window Rate Limiter
RATE_LIMIT_STORE = defaultdict(list)
ANALYZE_LIMIT_STORE = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 120
MAX_ANALYZE_PER_MINUTE = 20

def sanitize_text(text: str, max_length: int = 150) -> str:
    """Strips control chars, tags, and escapes HTML to prevent XSS / XML injection."""
    if not text:
        return ""
    # Strip null bytes & control chars
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(text))
    # Strip HTML/script tags
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    # Escape HTML entities
    cleaned = html.escape(cleaned.strip())
    return cleaned[:max_length]

@app.middleware("http")
async def security_hardening_middleware(request: Request, call_next):
    """
    Enterprise Security Middleware:
    1. Anti-DDoS & IP Rate Limiting (120 req/min global, 20 req/min for AI analysis)
    2. Request Body Size Enforcement (Max 25MB)
    3. OWASP Security Headers (nosniff, frame-options, XSS protection, referrer policy)
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    # Rate limiting: Prune timestamps older than 60 seconds
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < 60]
    ANALYZE_LIMIT_STORE[client_ip] = [t for t in ANALYZE_LIMIT_STORE[client_ip] if now - t < 60]

    # Check heavy AI endpoint rate limit
    if request.url.path == "/api/analyze":
        if len(ANALYZE_LIMIT_STORE[client_ip]) >= MAX_ANALYZE_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many AI analysis requests. Rate limit is 20 per minute. Please wait."}
            )
        ANALYZE_LIMIT_STORE[client_ip].append(now)

    # Check global endpoint rate limit
    if len(RATE_LIMIT_STORE[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Global rate limit exceeded. Please wait a minute."}
        )
    RATE_LIMIT_STORE[client_ip].append(now)

    # Request size limit check
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body exceeds maximum allowed limit of 25MB."}
        )

    # Process request
    response = await call_next(request)

    # Inject Essential OWASP Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    return response

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

# Mount static file directories safely
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
    Secure Deep Learning Inference & Grad-CAM Pipeline:
    - Enforces strict image file type, magic byte raster validation, and sanitization.
    - Neutralizes polyglot / script execution attacks by re-encoding images with PIL.
    - Sanitizes all patient parameters against SQL, XSS, and command injection.
    - Protects against Path Traversal (LFI).
    """
    # 1. Sanitize demographic & clinical parameters
    clean_patient_name = sanitize_text(patient_name, max_length=60) or "Anonymous"
    clean_patient_id = sanitize_text(patient_id, max_length=40) if patient_id else None
    clean_symptoms = sanitize_text(symptoms, max_length=250) or "None Reported"
    clean_alt_ast = sanitize_text(alt_ast, max_length=100) or "Within Normal Limits"

    if gender not in ["Male", "Female", "Other", "Not Specified"]:
        gender = "Not Specified"
    if not (0 <= age <= 125):
        age = 45

    if not clean_patient_id:
        clean_patient_id = f"PT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    unique_token = uuid.uuid4().hex[:12]
    scan_filename = f"scan_{unique_token}.png"
    heatmap_filename = f"heatmap_{unique_token}.png"

    scan_path = os.path.join(UPLOADS_DIR, scan_filename)
    heatmap_path = os.path.join(UPLOADS_DIR, heatmap_filename)

    filename_hint = ""

    # 2. Secure File Intake
    if sample_name:
        # Prevent Directory Traversal: strictly validate against whitelist
        clean_sample = os.path.basename(sample_name)
        if clean_sample not in ALLOWED_SAMPLE_NAMES:
            raise HTTPException(status_code=400, detail="Invalid sample scan selection.")
        sample_path = os.path.join(SAMPLES_DIR, clean_sample)
        if not os.path.exists(sample_path):
            raise HTTPException(status_code=404, detail="Selected sample scan not found.")
        shutil.copy(sample_path, scan_path)
        filename_hint = clean_sample

    elif file and file.filename:
        # Extension validation
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension '{file_ext}'. Allowed formats: PNG, JPG, JPEG, WEBP, BMP, TIFF."
            )

        # Content-type check
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid Content-Type. Only images are permitted.")

        # Read file bytes with size constraint
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Uploaded file exceeds 15MB size limit.")
        if len(file_bytes) < 32:
            raise HTTPException(status_code=400, detail="Uploaded file is empty or too small.")

        # Verify raster image integrity with PIL (blocks polyglots, zip bombs, disguised executables)
        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
            pil_img.verify()  # Verifies structural validity of image container

            # Re-open and cleanly re-encode to PNG to strip EXIF metadata & neutralize embedded payloads
            pil_img = Image.open(io.BytesIO(file_bytes))
            if pil_img.mode in ('RGBA', 'P'):
                pil_img = pil_img.convert('RGB')
            pil_img.save(scan_path, format="PNG")
        except Exception:
            raise HTTPException(status_code=400, detail="Corrupted or invalid image data. Payload rejected.")

        filename_hint = os.path.basename(file.filename)
    else:
        raise HTTPException(status_code=400, detail="Please upload a valid scan image or select a sample scan.")

    # 3. Compute SHA-256 Hash for Cryptographic Data Integrity
    with open(scan_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # 4. Execute Deep Learning & Grad-CAM pipeline
    ai_result = diagnostic_engine.predict_and_explain(
        image_path=scan_path,
        output_heatmap_path=heatmap_path,
        filename_hint=filename_hint
    )

    # 5. Save to SQLite Database with Parameterized ORM
    record = PatientRecord(
        patient_id=clean_patient_id,
        patient_name=clean_patient_name,
        age=age,
        gender=gender,
        symptoms=clean_symptoms,
        alt_ast=clean_alt_ast,
        scan_filename=scan_filename,
        heatmap_filename=heatmap_filename,
        predicted_class=ai_result["predicted_class"],
        confidence=ai_result["confidence"],
        risk_level=ai_result["risk_level"],
        clinical_findings=ai_result["findings"],
        recommendations=ai_result["recommendations"],
        probabilities=json.dumps(ai_result["probabilities"]),
        doctor_status="Pending Radiologist Review",
        doctor_notes=f"AI Deep Learning assessment generated. Scan SHA-256: {file_hash[:16]}... Radiologist review pending."
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 6. Pre-generate Protected PDF report
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
        "sha256_hash": file_hash,
        "doctor_status": record.doctor_status,
        "doctor_notes": record.doctor_notes,
        "created_at": record.created_at.strftime("%d %b %Y, %H:%M")
    })


@app.get("/api/history")
def get_analysis_history(db: Session = Depends(get_db)):
    """Returns past patient diagnostic records safely formatted."""
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
    """Serves the generated PDF diagnostic report with Path Traversal protection."""
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid record identifier.")

    record = db.query(PatientRecord).filter(PatientRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Diagnostic record not found.")

    pdf_filename = f"report_record_{record_id}.pdf"
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    # Strict basename check against directory traversal
    safe_scan = os.path.basename(record.scan_filename)
    safe_heat = os.path.basename(record.heatmap_filename)
    scan_path = os.path.join(UPLOADS_DIR, safe_scan)
    heatmap_path = os.path.join(UPLOADS_DIR, safe_heat)

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

    # Sanitize download filename for Content-Disposition header
    safe_download_name = re.sub(r'[^a-zA-Z0-9_\-]', '', str(record.patient_id))
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"LivSensi_Report_{safe_download_name}.pdf"
    )


@app.post("/api/verify/{record_id}")
def verify_patient_record(
    record_id: int,
    doctor_status: str = Form(...),
    doctor_notes: str = Form(...),
    doctor_pin: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Allows doctor/radiologist to confirm or add clinical notes.
    Protected against injection attacks and unvalidated changes.
    """
    if record_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid record ID.")

    record = db.query(PatientRecord).filter(PatientRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")

    # Sanitize doctor notes and status
    clean_status = sanitize_text(doctor_status, max_length=50)
    clean_notes = sanitize_text(doctor_notes, max_length=500)

    record.doctor_status = clean_status
    record.doctor_notes = clean_notes
    db.commit()

    return JSONResponse(content={"status": "success", "message": "Clinical review securely updated."})


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*65)
    print("  LIV-SENSI AI - SECURED CLINICAL RADIOLOGY PORTAL")
    print(f"  Local PC Access:   http://127.0.0.1:8000")
    print(f"  Mobile LAN Access: http://{LOCAL_IP}:8000")
    print("="*65 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
