from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional, Dict, Any, Union
import json
import logging
from datetime import datetime, date
import re

# Import database and models
from app.db.database import get_db
from app.models.patient import Patient
from app.models.prescription import Prescription

# Import services
from app.services.semantic_search import semantic_search_prescriptions
from app.services.drug_interactions import search_drug_database, get_drug_info, check_drug_interactions  # Added missing import

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def parse_date(date_str: Optional[str], param_name: str) -> Optional[date]:
    """Helper function to parse and validate date strings."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD"
        )

def extract_medications_from_prescription(prescription: Prescription) -> List[Dict[str, Any]]:
    """Extract and normalize medications from prescription data."""
    try:
        medications = []
        
        # Try to get medications from JSON field
        if prescription.medications:
            meds_data = (
                json.loads(prescription.medications)
                if isinstance(prescription.medications, str)
                else prescription.medications
            )
            if isinstance(meds_data, list):
                medications.extend(meds_data)
        
        # Try to get medications from parsed_data
        if prescription.parsed_data:
            parsed_data = (
                json.loads(prescription.parsed_data)
                if isinstance(prescription.parsed_data, str)
                else prescription.parsed_data
            )
            if isinstance(parsed_data, dict) and 'medications' in parsed_data:
                meds_from_parsed = parsed_data['medications']
                if isinstance(meds_from_parsed, list):
                    medications.extend(meds_from_parsed)
        
        # Normalize medication data
        normalized_meds = []
        for med in medications:
            if isinstance(med, dict):
                normalized_med = {
                    'name': med.get('name', med.get('drug_name', med.get('medication', ''))),
                    'dosage': med.get('dosage', med.get('dose', '')),
                    'frequency': med.get('frequency', med.get('freq', '')),
                    'duration': med.get('duration', ''),
                    'instructions': med.get('instructions', med.get('notes', ''))
                }
                if normalized_med['name']:
                    normalized_meds.append(normalized_med)
            elif isinstance(med, str) and med.strip():
                normalized_meds.append({
                    'name': med.strip(),
                    'dosage': '',
                    'frequency': '',
                    'duration': '',
                    'instructions': ''
                })
        
        return normalized_meds
    
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Error extracting medications from prescription {prescription.id}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error extracting medications from prescription {prescription.id}: {str(e)}")
        return []

def search_medications_in_text(search_term: str, text: str) -> bool:
    """Search for medication names in text using fuzzy matching."""
    if not search_term or not text:
        return False
    
    # Normalize search term and text
    search_term = search_term.lower().strip()
    text = text.lower()
    
    # Basic input validation to prevent regex issues
    if not re.match(r'^[\w\s\-]+$', search_term):
        return False
    
    # Direct substring match
    if search_term in text:
        return True
    
    # Word boundary match
    search_words = search_term.split()
    for word in search_words:
        if len(word) >= 3:  # Only search words with 3+ characters
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, text):
                return True
    
    return False

@router.get("/search/drugs")
async def search_drugs(
    q: str = Query(..., min_length=2, description="Search query for drug names"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    include_interactions: bool = Query(False, description="Include drug interaction information"),
    db: Session = Depends(get_db)
):
    """
    Search for drugs in the database and external drug databases.
    
    Parameters:
    - q: Search query (drug name or partial name)
    - limit: Maximum number of results to return
    - include_interactions: Whether to include interaction information
    """
    try:
        logger.info(f"Searching for drugs with query: '{q}'")
        
        search_term = q.strip()
        if not re.match(r'^[\w\s\-]+$', search_term):  # Basic input validation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters"
            )
        
        # Search in prescription database with filtering
        prescription_results = []
        try:
            # Use database-level filtering for better performance
            prescriptions = (
                db.query(Prescription)
                .filter(
                    or_(
                        Prescription.medications.ilike(f"%{search_term}%"),
                        Prescription.raw_text.ilike(f"%{search_term}%")
                    )
                )
                .limit(limit * 2)  # Buffer to account for duplicates
                .all()
            )
            
            found_medications = set()  # Use set to avoid duplicates
            prescription_matches = []
            
            for prescription in prescriptions:
                medications = extract_medications_from_prescription(prescription)
                
                for med in medications:
                    med_name = med.get('name', '').lower()
                    if search_medications_in_text(search_term, med_name):
                        found_medications.add(med_name.title())
                        prescription_matches.append({
                            'prescription_id': prescription.id,
                            'patient_id': prescription.patient_id,
                            'medication': med,
                            'doctor_name': prescription.doctor_name,
                            'prescription_date': prescription.prescription_date.isoformat() if prescription.prescription_date else None
                        })
                
                # Also search in raw text
                if prescription.raw_text and search_medications_in_text(search_term, prescription.raw_text):
                    prescription_matches.append({
                        'prescription_id': prescription.id,
                        'patient_id': prescription.patient_id,
                        'match_type': 'raw_text',
                        'doctor_name': prescription.doctor_name,
                        'prescription_date': prescription.prescription_date.isoformat() if prescription.prescription_date else None
                    })
            
            prescription_results = {
                'found_medications': list(found_medications),
                'prescription_matches': prescription_matches[:limit],
                'total_matches': len(prescription_matches)
            }
            
        except Exception as e:
            logger.error(f"Error searching prescriptions: {str(e)}")
            prescription_results = {'error': 'Failed to search prescription database'}
        
        # Search external drug database
        external_results = []
        try:
            external_drugs = search_drug_database(search_term, limit=limit)
            external_results = external_drugs
        except Exception as e:
            logger.error(f"Error searching external drug database: {str(e)}")
            external_results = []
        
        # Get drug information if requested
        drug_info = {}
        if include_interactions and prescription_results.get('found_medications'):
            for med_name in prescription_results['found_medications'][:5]:  # Limit to first 5
                try:
                    info = get_drug_info(med_name)
                    if info:
                        drug_info[med_name] = info
                except Exception as e:
                    logger.warning(f"Failed to get info for drug {med_name}: {str(e)}")
        
        response_data = {
            "success": True,
            "data": {
                "query": search_term,
                "prescription_database": prescription_results,
                "external_database": external_results,
                "drug_information": drug_info if include_interactions else {},
                "total_sources": 2,
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Drug search completed for '{search_term}' - found {len(prescription_results.get('found_medications', []))} unique drugs")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in drug search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search drugs: {str(e)}"
        )

@router.get("/search/prescriptions")
async def search_prescriptions(
    q: str = Query(..., min_length=2, description="Search query"),
    search_type: str = Query("all", regex="^(all|patient|doctor|medication|text)$", description="Type of search"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Search prescriptions by various criteria.
    
    Parameters:
    - q: Search query
    - search_type: Type of search (all, patient, doctor, medication, text)
    - skip: Number of records to skip for pagination
    - limit: Maximum number of results to return
    - start_date: Optional start date filter
    - end_date: Optional end date filter
    """
    try:
        logger.info(f"Searching prescriptions with query: '{q}', type: '{search_type}'")
        
        search_term = q.strip()
        if not re.match(r'^[\w\s\-]+$', search_term):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters"
            )
        
        # Build base query
        query = db.query(Prescription).join(Patient, isouter=True)  # Use outer join to handle missing patients
        
        # Apply date filters
        start_date_obj = parse_date(start_date, "start_date")
        if start_date_obj:
            query = query.filter(Prescription.prescription_date >= start_date_obj)
        
        end_date_obj = parse_date(end_date, "end_date")
        if end_date_obj:
            query = query.filter(Prescription.prescription_date <= end_date_obj)
        
        # Apply search filters based on search type
        search_pattern = f"%{search_term}%"
        
        if search_type == "all":
            query = query.filter(
                or_(
                    Patient.name.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern),
                    Prescription.doctor_name.ilike(search_pattern),
                    Prescription.raw_text.ilike(search_pattern),
                    Prescription.medications.ilike(search_pattern),
                    Prescription.parsed_data.ilike(search_pattern)
                )
            )
        elif search_type == "patient":
            query = query.filter(
                or_(
                    Patient.name.ilike(search_pattern),
                    Patient.phone.ilike(search_pattern)
                )
            )
        elif search_type == "doctor":
            query = query.filter(Prescription.doctor_name.ilike(search_pattern))
        elif search_type == "medication":
            query = query.filter(
                or_(
                    Prescription.medications.ilike(search_pattern),
                    Prescription.parsed_data.ilike(search_pattern)
                )
            )
        elif search_type == "text":
            query = query.filter(Prescription.raw_text.ilike(search_pattern))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        prescriptions = query.order_by(desc(Prescription.created_at)).offset(skip).limit(limit).all()
        
        # Serialize results
        results = []
        for prescription in prescriptions:
            patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
            
            medications = extract_medications_from_prescription(prescription)
            
            parsed_data = {}
            if prescription.parsed_data:
                try:
                    parsed_data = (
                        json.loads(prescription.parsed_data)
                        if isinstance(prescription.parsed_data, str)
                        else prescription.parsed_data
                    )
                except (json.JSONDecodeError, TypeError):
                    parsed_data = {}
            
            result = {
                "prescription_id": prescription.id,
                "patient": {
                    "id": patient.id if patient else None,
                    "name": patient.name if patient else "Unknown",
                    "phone": patient.phone if patient else None
                },
                "doctor_name": prescription.doctor_name,
                "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                "created_at": prescription.created_at.isoformat() if prescription.created_at else None,
                "medications": medications,
                "medication_count": len(medications),
                "raw_text_preview": (
                    prescription.raw_text[:200] + "..." if prescription.raw_text and len(prescription.raw_text) > 200
                    else prescription.raw_text or ""
                ),
                "parsed_data": parsed_data,
                "match_score": 1.0  # Placeholder; could integrate actual scoring
            }
            
            results.append(result)
        
        response_data = {
            "success": True,
            "data": {
                "query": search_term,
                "search_type": search_type,
                "results": results,
                "total_count": total_count,
                "returned_count": len(results),
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(results)) < total_count,
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Prescription search completed - found {total_count} total matches, returned {len(results)}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prescription search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search prescriptions: {str(e)}"
        )

@router.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., min_length=3, description="Search query for semantic search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    threshold: float = Query(0.7, ge=0.1, le=1.0, description="Similarity threshold for results"),
    search_type: str = Query("all", regex="^(all|prescriptions|medications|symptoms)$", description="Type of semantic search"),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across prescriptions and medications.
    
    Parameters:
    - q: Search query for semantic matching
    - limit: Maximum number of results to return
    - threshold: Minimum similarity score for results
    - search_type: Type of semantic search (all, prescriptions, medications, symptoms)
    """
    try:
        logger.info(f"Performing semantic search with query: '{q}', type: '{search_type}'")
        
        search_term = q.strip()
        if not re.match(r'^[\w\s\-]+$', search_term):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters"
            )
        
        # Perform semantic search using the service
        try:
            semantic_results = semantic_search_prescriptions(
                query=search_term,
                limit=limit,
                threshold=threshold,
                search_type=search_type
            )
        except Exception as e:
            logger.error(f"Semantic search service error: {str(e)}")
            semantic_results = []
        
        # Get prescription details for semantic results
        results = []
        if semantic_results:
            prescription_ids = [
                result.get('prescription_id') for result in semantic_results
                if result.get('prescription_id')
            ]
            
            if prescription_ids:
                prescriptions = db.query(Prescription).filter(
                    Prescription.id.in_(prescription_ids)
                ).all()
                
                prescription_map = {p.id: p for p in prescriptions}
                
                for semantic_result in semantic_results:
                    prescription_id = semantic_result.get('prescription_id')
                    prescription = prescription_map.get(prescription_id)
                    
                    if prescription:
                        patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
                        medications = extract_medications_from_prescription(prescription)
                        
                        result = {
                            "prescription_id": prescription.id,
                            "patient": {
                                "id": patient.id if patient else None,
                                "name": patient.name if patient else "Unknown",
                                "phone": patient.phone if patient else None
                            },
                            "doctor_name": prescription.doctor_name,
                            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                            "medications": medications,
                            "similarity_score": semantic_result.get('score', 0.0),
                            "matched_text": semantic_result.get('matched_text', ''),
                            "match_type": semantic_result.get('match_type', 'unknown'),
                            "raw_text_preview": (
                                prescription.raw_text[:200] + "..." if prescription.raw_text and len(prescription.raw_text) > 200
                                else prescription.raw_text or ""
                            )
                        }
                        results.append(result)
        
        response_data = {
            "success": True,
            "data": {
                "query": search_term,
                "search_type": search_type,
                "results": results,
                "total_count": len(results),
                "threshold": threshold,
                "semantic_search_available": bool(semantic_results),
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Semantic search completed for '{search_term}' - found {len(results)} results")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic search: {str(e)}"
        )

@router.get("/search/medications/interactions")
async def search_medication_interactions(
    medications: str = Query(..., description="Comma-separated list of medication names"),
    severity: str = Query("all", regex="^(all|major|moderate|minor)$", description="Filter by interaction severity"),
    db: Session = Depends(get_db)
):
    """
    Search for interactions between medications.
    
    Parameters:
    - medications: Comma-separated list of medication names
    - severity: Filter by interaction severity (all, major, moderate, minor)
    """
    try:
        logger.info(f"Searching medication interactions for: '{medications}'")
        
        # Parse and validate medication list
        med_list = [med.strip() for med in medications.split(',') if med.strip() and re.match(r'^[\w\s\-]+$', med.strip())]
        if len(med_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 valid medication names are required for interaction search"
            )
        
        # Search for interactions using the service
        try:
            interactions = check_drug_interactions(med_list, severity_filter=severity)
        except Exception as e:
            logger.error(f"Drug interaction service error: {str(e)}")
            interactions = []
        
        # Get additional drug information
        drug_info = {}
        for med_name in med_list:
            try:
                info = get_drug_info(med_name)
                if info:
                    drug_info[med_name] = info
            except Exception as e:
                logger.warning(f"Failed to get info for drug {med_name}: {str(e)}")
        
        response_data = {
            "success": True,
            "data": {
                "medications": med_list,
                "interactions": interactions,
                "drug_information": drug_info,
                "severity_filter": severity,
                "total_interactions": len(interactions),
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Medication interaction search completed - found {len(interactions)} interactions")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in medication interaction search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search medication interactions: {str(e)}"
        )

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    type: str = Query("all", regex="^(all|drugs|doctors|patients)$", description="Type of suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial query.
    
    Parameters:
    - q: Partial search query
    - type: Type of suggestions (all, drugs, doctors, patients)
    - limit: Maximum number of suggestions to return
    """
    try:
        logger.info(f"Getting search suggestions for: '{q}', type: '{type}'")
        
        search_term = q.strip().lower()
        if not re.match(r'^[\w\s\-]+$', search_term):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters"
            )
        
        suggestions = []
        
        # Calculate limit per category for 'all' type
        category_limit = limit // 3 if type == "all" else limit
        
        if type in ["all", "drugs"]:
            try:
                prescriptions = (
                    db.query(Prescription)
                    .filter(Prescription.medications.ilike(f"%{search_term}%"))
                    .limit(category_limit * 2)  # Buffer for duplicates
                    .all()
                )
                found_drugs = set()
                
                for prescription in prescriptions:
                    medications = extract_medications_from_prescription(prescription)
                    for med in medications:
                        med_name = med.get('name', '').lower()
                        if med_name and search_term in med_name:
                            found_drugs.add(med.get('name', '').title())
                
                for drug in list(found_drugs)[:category_limit]:
                    suggestions.append({
                        "text": drug,
                        "type": "drug",
                        "category": "medication"
                    })
            except Exception as e:
                logger.warning(f"Error getting drug suggestions: {str(e)}")
        
        if type in ["all", "doctors"]:
            try:
                doctors = (
                    db.query(Prescription.doctor_name)
                    .filter(Prescription.doctor_name.ilike(f"%{search_term}%"))
                    .distinct()
                    .limit(category_limit)
                    .all()
                )
                
                for doctor in doctors:
                    if doctor[0]:
                        suggestions.append({
                            "text": doctor[0],
                            "type": "doctor",
                            "category": "healthcare_provider"
                        })
            except Exception as e:
                logger.warning(f"Error getting doctor suggestions: {str(e)}")
        
        if type in ["all", "patients"]:
            try:
                patients = (
                    db.query(Patient.name)
                    .filter(Patient.name.ilike(f"%{search_term}%"))
                    .limit(category_limit)
                    .all()
                )
                
                for patient in patients:
                    if patient[0]:
                        suggestions.append({
                            "text": patient[0],
                            "type": "patient",
                            "category": "patient"
                        })
            except Exception as e:
                logger.warning(f"Error getting patient suggestions: {str(e)}")
        
        # Sort suggestions by relevance
        suggestions.sort(key=lambda x: (
            0 if search_term == x["text"].lower() else 1,
            0 if x["text"].lower().startswith(search_term) else 1,
            x["text"].lower()
        ))
        
        response_data = {
            "success": True,
            "data": {
                "query": q,
                "suggestions": suggestions[:limit],
                "total_count": len(suggestions),
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Search suggestions completed for '{q}' - found {len(suggestions)} suggestions")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search suggestions: {str(e)}"
        )

@router.get("/search/advanced")
async def advanced_search(
    q: str = Query(..., min_length=2, description="Search query"),
    patient_name: Optional[str] = Query(None, description="Filter by patient name"),
    doctor_name: Optional[str] = Query(None, description="Filter by doctor name"),
    medication_name: Optional[str] = Query(None, description="Filter by medication name"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    has_interactions: Optional[bool] = Query(None, description="Filter prescriptions with drug interactions"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Advanced search with multiple filters.
    
    Parameters:
    - q: Main search query
    - patient_name: Filter by patient name
    - doctor_name: Filter by doctor name
    - medication_name: Filter by medication name
    - start_date: Start date filter
    - end_date: End date filter
    - has_interactions: Filter by interaction status
    - skip: Number of records to skip
    - limit: Maximum number of results
    """
    try:
        logger.info(f"Performing advanced search with query: '{q}'")
        
        search_term = q.strip()
        if not re.match(r'^[\w\s\-]+$', search_term):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query contains invalid characters"
            )
        
        # Build complex query
        query = db.query(Prescription).join(Patient, isouter=True)
        
        # Apply main search
        search_pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Patient.name.ilike(search_pattern),
                Prescription.doctor_name.ilike(search_pattern),
                Prescription.raw_text.ilike(search_pattern),
                Prescription.medications.ilike(search_pattern)
            )
        )
        
        # Apply additional filters
        if patient_name and re.match(r'^[\w\s\-]+$', patient_name):
            query = query.filter(Patient.name.ilike(f"%{patient_name}%"))
        
        if doctor_name and re.match(r'^[\w\s\-]+$', doctor_name):
            query = query.filter(Prescription.doctor_name.ilike(f"%{doctor_name}%"))
        
        if medication_name and re.match(r'^[\w\s\-]+$', medication_name):
            query = query.filter(
                or_(
                    Prescription.medications.ilike(f"%{medication_name}%"),
                    Prescription.parsed_data.ilike(f"%{medication_name}%")
                )
            )
        
        # Apply date filters
        start_date_obj = parse_date(start_date, "start_date")
        if start_date_obj:
            query = query.filter(Prescription.prescription_date >= start_date_obj)
        
        end_date_obj = parse_date(end_date, "end_date")
        if end_date_obj:
            query = query.filter(Prescription.prescription_date <= end_date_obj)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        prescriptions = query.order_by(desc(Prescription.created_at)).offset(skip).limit(limit).all()
        
        # Process results
        results = []
        for prescription in prescriptions:
            patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
            medications = extract_medications_from_prescription(prescription)
            
            # Check for interactions if requested
            has_interaction = False
            if has_interactions is not None:
                try:
                    med_names = [med.get('name', '') for med in medications if med.get('name')]
                    if len(med_names) >= 2:
                        interactions = check_drug_interactions(med_names)
                        has_interaction = len(interactions) > 0
                except Exception:
                    has_interaction = False
                
                # Skip if doesn't match interaction filter
                if has_interactions and not has_interaction:
                    continue
                if has_interactions is False and has_interaction:
                    continue
            
            result = {
                "prescription_id": prescription.id,
                "patient": {
                    "id": patient.id if patient else None,
                    "name": patient.name if patient else "Unknown",
                    "phone": patient.phone if patient else None
                },
                "doctor_name": prescription.doctor_name,
                "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                "medications": medications,
                "medication_count": len(medications),
                "has_interactions": has_interaction,
                "raw_text_preview": (
                    prescription.raw_text[:200] + "..." if prescription.raw_text and len(prescription.raw_text) > 200
                    else prescription.raw_text or ""
                )
            }
            results.append(result)
        
        response_data = {
            "success": True,
            "data": {
                "query": search_term,
                "results": results,
                "total_count": total_count,
                "returned_count": len(results),
                "filters": {
                    "patient_name": patient_name,
                    "doctor_name": doctor_name,
                    "medication_name": medication_name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "has_interactions": has_interactions
                },
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "has_more": (skip + len(results)) < total_count
                },
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Advanced search completed - found {total_count} total matches, returned {len(results)}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform advanced search: {str(e)}"
        )