import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "liver_disease.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PatientRecord(Base):
    __tablename__ = "patient_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), index=True)
    patient_name = Column(String(100), default="Anonymous")
    age = Column(Integer, default=45)
    gender = Column(String(20), default="Not Specified")
    symptoms = Column(String(255), default="None Reported")
    alt_ast = Column(String(100), default="Normal")
    
    scan_filename = Column(String(255))
    heatmap_filename = Column(String(255))
    
    predicted_class = Column(String(100))
    confidence = Column(Float)
    risk_level = Column(String(50))
    clinical_findings = Column(Text)
    recommendations = Column(Text)
    probabilities = Column(Text)  # JSON formatted string
    
    doctor_status = Column(String(50), default="Pending Review")
    doctor_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
