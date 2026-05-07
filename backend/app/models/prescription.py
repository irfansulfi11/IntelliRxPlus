from sqlalchemy import Column, Integer, ForeignKey, Text, JSON, DateTime, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class Prescription(Base):
    __tablename__ = "prescriptions"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    text_raw = Column(Text)
    structured_json = Column(JSON)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    patient = relationship("Patient", back_populates="prescriptions")