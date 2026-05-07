from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import logging

# Import database and models
from app.db.database import get_db
from app.models.patient import Patient
from app.models.prescription import Prescription

# Import services
from app.services.ocr import extract_text_from_image
from app.services.llm_parser import parse_prescription_text
from app.services.drug_interactions import check_drug_interactions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           '.' + filename.rsplit('.', 1)[1].lower() in [ext.lstrip('.') for ext in ALLOWED_EXTENSIONS]

def save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return the file path."""
    try:
        # Generate unique filename
        file_extension = upload_file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = upload_file.file.read()
            buffer.write(content)
        
        logger.info(f"File saved successfully: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

def get_or_create_patient(
    db: Session, 
    patient_name: str, 
    patient_phone: Optional[str] = None,
    patient_address: Optional[str] = None,
    patient_age: Optional[int] = None,
    patient_gender: Optional[str] = None
) -> Patient:
    """Get existing patient or create new one."""
    try:
        # First try to find existing patient by name and phone
        patient = None
        if patient_phone:
            patient = db.query(Patient).filter(
                Patient.name == patient_name,
                Patient.phone == patient_phone
            ).first()
        
        if not patient:
            # Try to find by name only if phone not provided or no match found
            patient = db.query(Patient).filter(Patient.name == patient_name).first()
        
        if not patient:
            # Create new patient
            patient = Patient(
                name=patient_name,
                phone=patient_phone,
                address=patient_address,
                age=patient_age,
                gender=patient_gender,
                created_at=datetime.utcnow()
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            logger.info(f"Created new patient: {patient.name} (ID: {patient.id})")
        else:
            # Update existing patient info if provided
            updated = False
            if patient_phone and patient.phone != patient_phone:
                patient.phone = patient_phone
                updated = True
            if patient_address and patient.address != patient_address:
                patient.address = patient_address
                updated = True
            if patient_age and patient.age != patient_age:
                patient.age = patient_age
                updated = True
            if patient_gender and patient.gender != patient_gender:
                patient.gender = patient_gender
                updated = True
            
            if updated:
                db.commit()
                db.refresh(patient)
                logger.info(f"Updated existing patient: {patient.name} (ID: {patient.id})")
        
        return patient
    
    except Exception as e:
        logger.error(f"Error handling patient: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle patient data: {str(e)}"
        )

def create_prescription_record(
    db: Session,
    patient_id: int,
    image_path: str,
    raw_text: str,
    parsed_data: Dict[str, Any],
    medications: List[Dict[str, Any]],
    doctor_name: Optional[str] = None,
    prescription_date: Optional[date] = None
) -> Prescription:
    """Create a new prescription record in the database."""
    try:
        prescription = Prescription(
            patient_id=patient_id,
            image_path=image_path,
            raw_text=raw_text,
            parsed_data=json.dumps(parsed_data),
            medications=json.dumps(medications),
            doctor_name=doctor_name,
            prescription_date=prescription_date or date.today(),
            created_at=datetime.utcnow()
        )
        
        db.add(prescription)
        db.commit()
        db.refresh(prescription)
        
        logger.info(f"Created prescription record (ID: {prescription.id}) for patient {patient_id}")
        return prescription
    
    except Exception as e:
        logger.error(f"Error creating prescription: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prescription record: {str(e)}"
        )

@router.post("/upload")
async def upload_prescription(
    file: UploadFile = File(...),
    patient_name: str = Form(...),
    patient_phone: Optional[str] = Form(None),
    patient_address: Optional[str] = Form(None),
    patient_age: Optional[int] = Form(None),
    patient_gender: Optional[str] = Form(None),
    doctor_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process prescription image.
    
    This endpoint:
    1. Validates the uploaded file
    2. Saves the file to disk
    3. Extracts text using OCR
    4. Parses the text using LLM
    5. Creates/updates patient record
    6. Creates prescription record
    7. Checks for drug interactions
    8. Returns processed data
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Validate required fields
        if not patient_name or patient_name.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient name is required"
            )
        
        logger.info(f"Processing prescription upload for patient: {patient_name}")
        
        # Save uploaded file
        file_path = save_uploaded_file(file)
        
        # Extract text from image using OCR
        logger.info("Extracting text from image using OCR...")
        raw_text = extract_text_from_image(file_path)
        
        if not raw_text or raw_text.strip() == "":
            # Clean up file if OCR failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract readable text from the image. Please ensure the image is clear and contains text."
            )
        
        logger.info(f"Extracted text length: {len(raw_text)} characters")
        
        # Parse text using LLM
        logger.info("Parsing extracted text using LLM...")
        parsed_data = parse_prescription_text(raw_text)
        
        if not parsed_data:
            # Clean up file if parsing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse prescription text. Please try with a clearer image."
            )
        
        # Extract medications from parsed data
        medications = parsed_data.get('medications', [])
        if not medications:
            logger.warning("No medications found in parsed data")
        
        # Get or create patient
        patient = get_or_create_patient(
            db=db,
            patient_name=patient_name.strip(),
            patient_phone=patient_phone.strip() if patient_phone else None,
            patient_address=patient_address.strip() if patient_address else None,
            patient_age=patient_age,
            patient_gender=patient_gender.strip() if patient_gender else None
        )
        
        # Parse prescription date from parsed data or form
        prescription_date = None
        if 'prescription_date' in parsed_data and parsed_data['prescription_date']:
            try:
                prescription_date = datetime.strptime(
                    parsed_data['prescription_date'], 
                    '%Y-%m-%d'
                ).date()
            except (ValueError, TypeError):
                prescription_date = date.today()
        else:
            prescription_date = date.today()
        
        # Create prescription record
        prescription = create_prescription_record(
            db=db,
            patient_id=patient.id,
            image_path=file_path,
            raw_text=raw_text,
            parsed_data=parsed_data,
            medications=medications,
            doctor_name=doctor_name.strip() if doctor_name else parsed_data.get('doctor_name'),
            prescription_date=prescription_date
        )
        
        # Check for drug interactions
        interactions = []
        if medications and len(medications) > 1:
            try:
                logger.info("Checking for drug interactions...")
                interactions = check_drug_interactions(medications)
            except Exception as e:
                logger.warning(f"Drug interaction check failed: {str(e)}")
                # Don't fail the entire request if interaction check fails
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "Prescription processed successfully",
            "data": {
                "prescription_id": prescription.id,
                "patient": {
                    "id": patient.id,
                    "name": patient.name,
                    "phone": patient.phone,
                    "address": patient.address,
                    "age": patient.age,
                    "gender": patient.gender
                },
                "prescription": {
                    "id": prescription.id,
                    "doctor_name": prescription.doctor_name,
                    "prescription_date": prescription.prescription_date.isoformat(),
                    "created_at": prescription.created_at.isoformat()
                },
                "extracted_text": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
                "parsed_data": parsed_data,
                "medications": medications,
                "drug_interactions": interactions,
                "interaction_count": len(interactions) if interactions else 0
            }
        }
        
        logger.info(f"Successfully processed prescription for patient: {patient.name}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_prescription: {str(e)}")
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the prescription: {str(e)}"
        )