from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from typing import List, Optional, Dict, Any
import json
import logging
from datetime import datetime, date

# Import database and models
from app.db.database import get_db
from app.models.patient import Patient
from app.models.prescription import Prescription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def serialize_prescription(prescription: Prescription) -> Dict[str, Any]:
    """Convert prescription object to serializable dictionary."""
    try:
        # Parse JSON fields safely
        parsed_data = {}
        medications = []
        
        if prescription.parsed_data:
            try:
                parsed_data = json.loads(prescription.parsed_data) if isinstance(prescription.parsed_data, str) else prescription.parsed_data
            except (json.JSONDecodeError, TypeError):
                parsed_data = {}
        
        if prescription.medications:
            try:
                medications = json.loads(prescription.medications) if isinstance(prescription.medications, str) else prescription.medications
            except (json.JSONDecodeError, TypeError):
                medications = []
        
        return {
            "id": prescription.id,
            "patient_id": prescription.patient_id,
            "doctor_name": prescription.doctor_name,
            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
            "created_at": prescription.created_at.isoformat() if prescription.created_at else None,
            "image_path": prescription.image_path,
            "raw_text": prescription.raw_text[:200] + "..." if prescription.raw_text and len(prescription.raw_text) > 200 else prescription.raw_text,
            "parsed_data": parsed_data,
            "medications": medications,
            "medication_count": len(medications) if medications else 0
        }
    except Exception as e:
        logger.error(f"Error serializing prescription {prescription.id}: {str(e)}")
        return {
            "id": prescription.id,
            "patient_id": prescription.patient_id,
            "doctor_name": prescription.doctor_name,
            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
            "created_at": prescription.created_at.isoformat() if prescription.created_at else None,
            "error": "Failed to serialize prescription data"
        }

def serialize_patient(patient: Patient, include_prescriptions: bool = False) -> Dict[str, Any]:
    """Convert patient object to serializable dictionary."""
    try:
        patient_data = {
            "id": patient.id,
            "name": patient.name,
            "phone": patient.phone,
            "address": patient.address,
            "age": patient.age,
            "gender": patient.gender,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        }
        
        if include_prescriptions and hasattr(patient, 'prescriptions'):
            patient_data["prescriptions"] = [
                serialize_prescription(prescription) 
                for prescription in patient.prescriptions
            ]
            patient_data["prescription_count"] = len(patient.prescriptions)
        
        return patient_data
    except Exception as e:
        logger.error(f"Error serializing patient {patient.id}: {str(e)}")
        return {
            "id": patient.id,
            "name": patient.name,
            "error": "Failed to serialize patient data"
        }

@router.get("/patients")
async def get_all_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by patient name or phone"),
    db: Session = Depends(get_db)
):
    """
    Get all patients with optional search and pagination.
    
    Parameters:
    - skip: Number of records to skip for pagination
    - limit: Maximum number of records to return
    - search: Optional search term for patient name or phone
    """
    try:
        logger.info(f"Fetching patients - skip: {skip}, limit: {limit}, search: {search}")
        
        # Build query
        query = db.query(Patient)
        
        # Add search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Patient.name.ilike(search_term),
                    Patient.phone.ilike(search_term) if Patient.phone.isnot(None) else False
                )
            )
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        patients = query.order_by(desc(Patient.created_at)).offset(skip).limit(limit).all()
        
        # Serialize patients
        patient_list = [serialize_patient(patient) for patient in patients]
        
        response_data = {
            "success": True,
            "data": {
                "patients": patient_list,
                "total_count": total_count,
                "returned_count": len(patient_list),
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(patient_list)) < total_count
            }
        }
        
        logger.info(f"Successfully fetched {len(patient_list)} patients")
        return JSONResponse(content=response_data, status_code=200)
        
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patients: {str(e)}"
        )

@router.get("/patients/{patient_id}")
async def get_patient_by_id(
    patient_id: int,
    include_prescriptions: bool = Query(False, description="Include patient's prescriptions"),
    db: Session = Depends(get_db)
):
    """
    Get a specific patient by ID with optional prescription data.
    
    Parameters:
    - patient_id: The ID of the patient to retrieve
    - include_prescriptions: Whether to include prescription data
    """
    try:
        logger.info(f"Fetching patient {patient_id} - include_prescriptions: {include_prescriptions}")
        
        # Query patient
        query = db.query(Patient).filter(Patient.id == patient_id)
        
        if include_prescriptions:
            # Join with prescriptions if requested
            query = query.outerjoin(Prescription)
        
        patient = query.first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Get prescriptions separately if needed for better control
        if include_prescriptions:
            prescriptions = db.query(Prescription).filter(
                Prescription.patient_id == patient_id
            ).order_by(desc(Prescription.created_at)).all()
            
            # Manually add prescriptions to patient object
            patient.prescriptions = prescriptions
        
        patient_data = serialize_patient(patient, include_prescriptions)
        
        response_data = {
            "success": True,
            "data": {
                "patient": patient_data
            }
        }
        
        logger.info(f"Successfully fetched patient {patient_id}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch patient: {str(e)}"
        )

@router.get("/patients/{patient_id}/prescriptions")
async def get_patient_prescriptions(
    patient_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    doctor_name: Optional[str] = Query(None, description="Filter by doctor name"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get all prescriptions for a specific patient with filtering and pagination.
    
    Parameters:
    - patient_id: The ID of the patient
    - skip: Number of records to skip for pagination
    - limit: Maximum number of records to return
    - doctor_name: Optional filter by doctor name
    - start_date: Optional start date filter (YYYY-MM-DD format)
    - end_date: Optional end date filter (YYYY-MM-DD format)
    """
    try:
        logger.info(f"Fetching prescriptions for patient {patient_id}")
        
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {patient_id} not found"
            )
        
        # Build prescription query
        query = db.query(Prescription).filter(Prescription.patient_id == patient_id)
        
        # Add filters
        if doctor_name and doctor_name.strip():
            query = query.filter(Prescription.doctor_name.ilike(f"%{doctor_name.strip()}%"))
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Prescription.prescription_date >= start_date_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Prescription.prescription_date <= end_date_obj)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        prescriptions = query.order_by(desc(Prescription.created_at)).offset(skip).limit(limit).all()
        
        # Serialize prescriptions
        prescription_list = [serialize_prescription(prescription) for prescription in prescriptions]
        
        response_data = {
            "success": True,
            "data": {
                "patient": serialize_patient(patient),
                "prescriptions": prescription_list,
                "total_count": total_count,
                "returned_count": len(prescription_list),
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(prescription_list)) < total_count,
                "filters": {
                    "doctor_name": doctor_name,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }
        
        logger.info(f"Successfully fetched {len(prescription_list)} prescriptions for patient {patient_id}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prescriptions for patient {patient_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch prescriptions: {str(e)}"
        )

@router.get("/prescriptions/{prescription_id}")
async def get_prescription_by_id(
    prescription_id: int,
    include_patient: bool = Query(False, description="Include patient data"),
    db: Session = Depends(get_db)
):
    """
    Get a specific prescription by ID with optional patient data.
    
    Parameters:
    - prescription_id: The ID of the prescription to retrieve
    - include_patient: Whether to include patient data
    """
    try:
        logger.info(f"Fetching prescription {prescription_id}")
        
        prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
        
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID {prescription_id} not found"
            )
        
        prescription_data = serialize_prescription(prescription)
        
        response_data = {
            "success": True,
            "data": {
                "prescription": prescription_data
            }
        }
        
        # Include patient data if requested
        if include_patient:
            patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
            if patient:
                response_data["data"]["patient"] = serialize_patient(patient)
        
        logger.info(f"Successfully fetched prescription {prescription_id}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prescription {prescription_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch prescription: {str(e)}"
        )

@router.get("/history/recent")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100, description="Number of recent items to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent prescription activity across all patients.
    
    Parameters:
    - limit: Maximum number of recent prescriptions to return
    """
    try:
        logger.info(f"Fetching {limit} recent prescriptions")
        
        # Get recent prescriptions with patient data
        prescriptions = db.query(Prescription).join(Patient).order_by(
            desc(Prescription.created_at)
        ).limit(limit).all()
        
        # Serialize data
        recent_activity = []
        for prescription in prescriptions:
            prescription_data = serialize_prescription(prescription)
            # Add patient name for context
            if hasattr(prescription, 'patient'):
                prescription_data["patient_name"] = prescription.patient.name
            else:
                patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
                prescription_data["patient_name"] = patient.name if patient else "Unknown"
            
            recent_activity.append(prescription_data)
        
        response_data = {
            "success": True,
            "data": {
                "recent_prescriptions": recent_activity,
                "count": len(recent_activity),
                "limit": limit
            }
        }
        
        logger.info(f"Successfully fetched {len(recent_activity)} recent prescriptions")
        return JSONResponse(content=response_data, status_code=200)
        
    except Exception as e:
        logger.error(f"Error fetching recent activity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recent activity: {str(e)}"
        )