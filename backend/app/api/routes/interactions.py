from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional, Dict, Any, Union
import json
import logging
from datetime import datetime, date
from pydantic import BaseModel, Field

# Import database and models
from app.db.database import get_db
from app.models.patient import Patient
from app.models.prescription import Prescription

# Import services
from app.services.drug_interactions import (
    check_drug_interactions, 
    get_drug_info, 
    search_drug_database,
    get_interaction_severity,
    check_contraindications,
    get_alternative_medications
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class DrugInteractionRequest(BaseModel):
    medications: List[str] = Field(..., description="List of medication names to check for interactions")
    patient_id: Optional[int] = Field(None, description="Optional patient ID for context")
    severity_filter: Optional[str] = Field("all", description="Filter by severity: all, major, moderate, minor")
    include_alternatives: bool = Field(False, description="Include alternative medication suggestions")

class DrugInfoRequest(BaseModel):
    drug_name: str = Field(..., description="Name of the drug to get information about")
    include_interactions: bool = Field(True, description="Include interaction information")
    include_contraindications: bool = Field(True, description="Include contraindication information")

class PrescriptionInteractionRequest(BaseModel):
    prescription_id: int = Field(..., description="ID of the prescription to check for interactions")
    check_with_history: bool = Field(True, description="Check interactions with patient's medication history")

@router.post("/interactions/check")
async def check_interactions(
    request: DrugInteractionRequest,
    db: Session = Depends(get_db)
):
    """
    Check for interactions between multiple medications.
    
    Body:
    - medications: List of medication names
    - patient_id: Optional patient ID for additional context
    - severity_filter: Filter by interaction severity
    - include_alternatives: Whether to include alternative suggestions
    """
    try:
        logger.info(f"Checking interactions for medications: {request.medications}")
        
        if len(request.medications) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 medications are required for interaction checking"
            )
        
        # Get patient context if provided
        patient_context = None
        if request.patient_id:
            patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
            if patient:
                patient_context = {
                    "id": patient.id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "medical_conditions": patient.medical_conditions
                }
        
        # Check drug interactions
        interactions = []
        try:
            interactions = check_drug_interactions(
                medications=request.medications,
                severity_filter=request.severity_filter,
                patient_context=patient_context
            )
        except Exception as e:
            logger.error(f"Error checking drug interactions: {str(e)}")
            interactions = []
        
        # Get detailed drug information
        drug_details = {}
        for med_name in request.medications:
            try:
                drug_info = get_drug_info(med_name)
                if drug_info:
                    drug_details[med_name] = drug_info
            except Exception as e:
                logger.warning(f"Failed to get details for drug {med_name}: {str(e)}")
        
        # Get alternative medications if requested
        alternatives = {}
        if request.include_alternatives and interactions:
            for interaction in interactions:
                if interaction.get('severity') in ['major', 'moderate']:
                    for drug in interaction.get('drugs', []):
                        try:
                            alts = get_alternative_medications(drug, patient_context)
                            if alts:
                                alternatives[drug] = alts
                        except Exception as e:
                            logger.warning(f"Failed to get alternatives for {drug}: {str(e)}")
        
        # Calculate risk assessment
        risk_level = "low"
        total_interactions = len(interactions)
        major_interactions = len([i for i in interactions if i.get('severity') == 'major'])
        moderate_interactions = len([i for i in interactions if i.get('severity') == 'moderate'])
        
        if major_interactions > 0:
            risk_level = "high"
        elif moderate_interactions > 0:
            risk_level = "moderate"
        elif total_interactions > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        response_data = {
            "success": True,
            "data": {
                "medications": request.medications,
                "interactions": interactions,
                "drug_details": drug_details,
                "alternatives": alternatives if request.include_alternatives else {},
                "patient_context": patient_context,
                "risk_assessment": {
                    "overall_risk": risk_level,
                    "total_interactions": total_interactions,
                    "major_interactions": major_interactions,
                    "moderate_interactions": moderate_interactions,
                    "minor_interactions": total_interactions - major_interactions - moderate_interactions
                },
                "recommendations": generate_interaction_recommendations(interactions, risk_level),
                "check_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Interaction check completed - found {total_interactions} interactions, risk level: {risk_level}")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in interaction check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check drug interactions: {str(e)}"
        )

@router.post("/interactions/drug-info")
async def get_drug_information(
    request: DrugInfoRequest,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific drug.
    
    Body:
    - drug_name: Name of the drug
    - include_interactions: Include interaction information
    - include_contraindications: Include contraindication information
    """
    try:
        logger.info(f"Getting drug information for: {request.drug_name}")
        
        drug_name = request.drug_name.strip()
        if not drug_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Drug name is required"
            )
        
        # Get basic drug information
        drug_info = {}
        try:
            drug_info = get_drug_info(drug_name)
        except Exception as e:
            logger.error(f"Error getting drug info: {str(e)}")
            drug_info = {"name": drug_name, "error": "Information not available"}
        
        # Get interaction information if requested
        interactions = []
        if request.include_interactions:
            try:
                # Get common interactions for this drug
                interactions = check_drug_interactions([drug_name, "common_medications"])
                interactions = [i for i in interactions if drug_name.lower() in [d.lower() for d in i.get('drugs', [])]]
            except Exception as e:
                logger.warning(f"Failed to get interactions for {drug_name}: {str(e)}")
        
        # Get contraindications if requested
        contraindications = []
        if request.include_contraindications:
            try:
                contraindications = check_contraindications(drug_name)
            except Exception as e:
                logger.warning(f"Failed to get contraindications for {drug_name}: {str(e)}")
        
        # Search for the drug in prescription database
        prescription_usage = []
        try:
            prescriptions = db.query(Prescription).all()
            for prescription in prescriptions:
                medications = extract_medications_from_prescription(prescription)
                for med in medications:
                    if drug_name.lower() in med.get('name', '').lower():
                        patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
                        prescription_usage.append({
                            "prescription_id": prescription.id,
                            "patient_name": patient.name if patient else "Unknown",
                            "doctor_name": prescription.doctor_name,
                            "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                            "dosage": med.get('dosage', ''),
                            "frequency": med.get('frequency', '')
                        })
        except Exception as e:
            logger.warning(f"Failed to get prescription usage for {drug_name}: {str(e)}")
        
        response_data = {
            "success": True,
            "data": {
                "drug_name": drug_name,
                "drug_information": drug_info,
                "interactions": interactions if request.include_interactions else [],
                "contraindications": contraindications if request.include_contraindications else [],
                "prescription_usage": prescription_usage,
                "usage_statistics": {
                    "total_prescriptions": len(prescription_usage),
                    "unique_patients": len(set(p['patient_name'] for p in prescription_usage)),
                    "unique_doctors": len(set(p['doctor_name'] for p in prescription_usage if p['doctor_name']))
                },
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Drug information retrieved for {drug_name} - found {len(prescription_usage)} prescription usages")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug information: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get drug information: {str(e)}"
        )

@router.post("/interactions/prescription")
async def check_prescription_interactions(
    request: PrescriptionInteractionRequest,
    db: Session = Depends(get_db)
):
    """
    Check for interactions within a specific prescription and optionally with patient history.
    
    Body:
    - prescription_id: ID of the prescription to check
    - check_with_history: Whether to check against patient's medication history
    """
    try:
        logger.info(f"Checking prescription interactions for prescription ID: {request.prescription_id}")
        
        # Get the prescription
        prescription = db.query(Prescription).filter(Prescription.id == request.prescription_id).first()
        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found"
            )
        
        # Get patient information
        patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
        patient_context = None
        if patient:
            patient_context = {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "medical_conditions": patient.medical_conditions
            }
        
        # Extract medications from prescription
        current_medications = extract_medications_from_prescription(prescription)
        current_med_names = [med.get('name', '') for med in current_medications if med.get('name')]
        
        if len(current_med_names) < 2:
            logger.info(f"Prescription {request.prescription_id} has fewer than 2 medications, no internal interactions possible")
        
        # Check internal prescription interactions
        internal_interactions = []
        if len(current_med_names) >= 2:
            try:
                internal_interactions = check_drug_interactions(
                    medications=current_med_names,
                    patient_context=patient_context
                )
            except Exception as e:
                logger.error(f"Error checking internal interactions: {str(e)}")
        
        # Check interactions with patient history if requested
        history_interactions = []
        historical_medications = []
        if request.check_with_history and patient:
            try:
                # Get patient's other prescriptions
                other_prescriptions = db.query(Prescription).filter(
                    and_(
                        Prescription.patient_id == patient.id,
                        Prescription.id != request.prescription_id
                    )
                ).order_by(desc(Prescription.prescription_date)).limit(10).all()
                
                # Extract medications from history
                for other_prescription in other_prescriptions:
                    hist_meds = extract_medications_from_prescription(other_prescription)
                    for med in hist_meds:
                        if med.get('name'):
                            historical_medications.append({
                                "name": med.get('name'),
                                "prescription_id": other_prescription.id,
                                "prescription_date": other_prescription.prescription_date.isoformat() if other_prescription.prescription_date else None,
                                "doctor_name": other_prescription.doctor_name
                            })
                
                # Check interactions between current and historical medications
                if historical_medications:
                    hist_med_names = list(set([med['name'] for med in historical_medications]))
                    all_medications = current_med_names + hist_med_names
                    
                    if len(all_medications) >= 2:
                        all_interactions = check_drug_interactions(
                            medications=all_medications,
                            patient_context=patient_context
                        )
                        
                        # Filter to only interactions involving current medications
                        history_interactions = [
                            interaction for interaction in all_interactions
                            if any(med in current_med_names for med in interaction.get('drugs', []))
                            and any(med in hist_med_names for med in interaction.get('drugs', []))
                        ]
                        
            except Exception as e:
                logger.error(f"Error checking history interactions: {str(e)}")
        
        # Combine and analyze all interactions
        all_interactions = internal_interactions + history_interactions
        
        # Calculate risk assessment
        risk_assessment = calculate_prescription_risk(all_interactions, current_medications, patient_context)
        
        # Generate recommendations
        recommendations = generate_prescription_recommendations(
            prescription, 
            all_interactions, 
            risk_assessment,
            patient_context
        )
        
        response_data = {
            "success": True,
            "data": {
                "prescription_id": request.prescription_id,
                "patient": patient_context,
                "current_medications": current_medications,
                "interactions": {
                    "internal": internal_interactions,
                    "with_history": history_interactions,
                    "total": all_interactions
                },
                "historical_medications": historical_medications if request.check_with_history else [],
                "risk_assessment": risk_assessment,
                "recommendations": recommendations,
                "prescription_details": {
                    "doctor_name": prescription.doctor_name,
                    "prescription_date": prescription.prescription_date.isoformat() if prescription.prescription_date else None,
                    "created_at": prescription.created_at.isoformat() if prescription.created_at else None
                },
                "check_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Prescription interaction check completed - found {len(all_interactions)} total interactions")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking prescription interactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check prescription interactions: {str(e)}"
        )

@router.get("/interactions/patient/{patient_id}")
async def get_patient_interactions(
    patient_id: int,
    include_resolved: bool = Query(False, description="Include resolved/historical interactions"),
    severity_filter: str = Query("all", regex="^(all|major|moderate|minor)$", description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of interactions to return"),
    db: Session = Depends(get_db)
):
    """
    Get all drug interactions for a specific patient across all their prescriptions.
    
    Parameters:
    - patient_id: ID of the patient
    - include_resolved: Include historical/resolved interactions
    - severity_filter: Filter by interaction severity
    - limit: Maximum number of interactions to return
    """
    try:
        logger.info(f"Getting patient interactions for patient ID: {patient_id}")
        
        # Get patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        patient_context = {
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "medical_conditions": patient.medical_conditions
        }
        
        # Get all patient prescriptions
        prescriptions = db.query(Prescription).filter(
            Prescription.patient_id == patient_id
        ).order_by(desc(Prescription.prescription_date)).all()
        
        if not prescriptions:
            return JSONResponse(content={
                "success": True,
                "data": {
                    "patient": patient_context,
                    "interactions": [],
                    "prescriptions": [],
                    "summary": {
                        "total_interactions": 0,
                        "active_interactions": 0,
                        "resolved_interactions": 0
                    }
                }
            }, status_code=200)
        
        # Extract all medications across all prescriptions
        all_medications = []
        prescription_medications = {}
        
        for prescription in prescriptions:
            medications = extract_medications_from_prescription(prescription)
            prescription_medications[prescription.id] = {
                "prescription": prescription,
                "medications": medications
            }
            
            for med in medications:
                if med.get('name'):
                    all_medications.append({
                        "name": med.get('name'),
                        "prescription_id": prescription.id,
                        "prescription_date": prescription.prescription_date,
                        "doctor_name": prescription.doctor_name,
                        "dosage": med.get('dosage', ''),
                        "frequency": med.get('frequency', ''),
                        "duration": med.get('duration', '')
                    })
        
        # Check for interactions across all medications
        unique_med_names = list(set([med['name'] for med in all_medications]))
        all_interactions = []
        
        if len(unique_med_names) >= 2:
            try:
                interactions = check_drug_interactions(
                    medications=unique_med_names,
                    severity_filter=severity_filter,
                    patient_context=patient_context
                )
                
                # Enhance interactions with prescription context
                for interaction in interactions:
                    enhanced_interaction = interaction.copy()
                    enhanced_interaction['prescriptions_involved'] = []
                    
                    for drug in interaction.get('drugs', []):
                        involved_meds = [med for med in all_medications if med['name'].lower() == drug.lower()]
                        for med in involved_meds:
                            enhanced_interaction['prescriptions_involved'].append({
                                "prescription_id": med['prescription_id'],
                                "prescription_date": med['prescription_date'].isoformat() if med['prescription_date'] else None,
                                "doctor_name": med['doctor_name'],
                                "medication_details": med
                            })
                    
                    all_interactions.append(enhanced_interaction)
                    
            except Exception as e:
                logger.error(f"Error checking patient interactions: {str(e)}")
        
        # Categorize interactions (active vs resolved)
        active_interactions = []
        resolved_interactions = []
        current_date = datetime.now().date()
        
        for interaction in all_interactions:
            # Consider interaction active if any involved prescription is recent (within 90 days)
            is_active = False
            for prescription_info in interaction.get('prescriptions_involved', []):
                if prescription_info.get('prescription_date'):
                    try:
                        prescription_date = datetime.fromisoformat(prescription_info['prescription_date']).date()
                        days_diff = (current_date - prescription_date).days
                        if days_diff <= 90:  # Consider active if within 90 days
                            is_active = True
                            break
                    except:
                        pass
            
            if is_active:
                active_interactions.append(interaction)
            else:
                resolved_interactions.append(interaction)
        
        # Filter interactions based on include_resolved parameter
        filtered_interactions = active_interactions
        if include_resolved:
            filtered_interactions.extend(resolved_interactions)
        
        # Apply limit
        filtered_interactions = filtered_interactions[:limit]
        
        # Generate summary statistics
        summary = {
            "total_interactions": len(all_interactions),
            "active_interactions": len(active_interactions),
            "resolved_interactions": len(resolved_interactions),
            "severity_breakdown": {
                "major": len([i for i in filtered_interactions if i.get('severity') == 'major']),
                "moderate": len([i for i in filtered_interactions if i.get('severity') == 'moderate']),
                "minor": len([i for i in filtered_interactions if i.get('severity') == 'minor'])
            },
            "total_prescriptions": len(prescriptions),
            "total_medications": len(all_medications),
            "unique_medications": len(unique_med_names)
        }
        
        response_data = {
            "success": True,
            "data": {
                "patient": patient_context,
                "interactions": filtered_interactions,
                "prescriptions": [
                    {
                        "id": p.id,
                        "doctor_name": p.doctor_name,
                        "prescription_date": p.prescription_date.isoformat() if p.prescription_date else None,
                        "medication_count": len(prescription_medications[p.id]["medications"]),
                        "medications": prescription_medications[p.id]["medications"]
                    }
                    for p in prescriptions
                ],
                "summary": summary,
                "filters": {
                    "include_resolved": include_resolved,
                    "severity_filter": severity_filter
                },
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Patient interactions retrieved for {patient.name} - found {len(filtered_interactions)} interactions")
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient interactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patient interactions: {str(e)}"
        )

# Helper functions
def extract_medications_from_prescription(prescription: Prescription) -> List[Dict[str, Any]]:
    """Extract and normalize medications from prescription data."""
    try:
        medications = []
        
        # Try to get medications from JSON field
        if prescription.medications:
            try:
                meds_data = json.loads(prescription.medications) if isinstance(prescription.medications, str) else prescription.medications
                if isinstance(meds_data, list):
                    medications.extend(meds_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Try to get medications from parsed_data
        if prescription.parsed_data:
            try:
                parsed_data = json.loads(prescription.parsed_data) if isinstance(prescription.parsed_data, str) else prescription.parsed_data
                if isinstance(parsed_data, dict) and 'medications' in parsed_data:
                    meds_from_parsed = parsed_data['medications']
                    if isinstance(meds_from_parsed, list):
                        medications.extend(meds_from_parsed)
            except (json.JSONDecodeError, TypeError):
                pass
        
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
            elif isinstance(med, str):
                normalized_meds.append({
                    'name': med,
                    'dosage': '',
                    'frequency': '',
                    'duration': '',
                    'instructions': ''
                })
        
        return normalized_meds
    
    except Exception as e:
        logger.error(f"Error extracting medications from prescription {prescription.id}: {str(e)}")
        return []

def generate_interaction_recommendations(interactions: List[Dict], risk_level: str) -> List[str]:
    """Generate recommendations based on drug interactions."""
    recommendations = []
    
    if risk_level == "high":
        recommendations.append("⚠️ HIGH RISK: Immediate medical consultation recommended")
        recommendations.append("Consider alternative medications or dosage adjustments")
        recommendations.append("Monitor patient closely for adverse effects")
    elif risk_level == "moderate":
        recommendations.append("⚠️ MODERATE RISK: Medical review recommended")
        recommendations.append("Monitor for interaction symptoms")
        recommendations.append("Consider timing separation of medications")
    elif risk_level == "low":
        recommendations.append("ℹ️ LOW RISK: Routine monitoring sufficient")
        recommendations.append("Educate patient about potential mild interactions")
    else:
        recommendations.append("✅ MINIMAL RISK: No specific precautions needed")
    
    # Add specific recommendations based on interaction types
    major_interactions = [i for i in interactions if i.get('severity') == 'major']
    if major_interactions:
        recommendations.append("Review major interactions with prescribing physician")
        recommendations.append("Consider therapeutic drug monitoring if available")
    
    return recommendations

def calculate_prescription_risk(interactions: List[Dict], medications: List[Dict], patient_context: Dict) -> Dict:
    """Calculate risk assessment for a prescription."""
    total_interactions = len(interactions)
    major_count = len([i for i in interactions if i.get('severity') == 'major'])
    moderate_count = len([i for i in interactions if i.get('severity') == 'moderate'])
    minor_count = total_interactions - major_count - moderate_count
    
    # Determine overall risk
    if major_count > 0:
        overall_risk = "high"
    elif moderate_count > 0:
        overall_risk = "moderate"
    elif minor_count > 0:
        overall_risk = "low"
    else:
        overall_risk = "minimal"
    
    # Consider patient factors
    risk_factors = []
    if patient_context:
        if patient_context.get('age', 0) > 65:
            risk_factors.append("Advanced age (>65)")
        if patient_context.get('medical_conditions'):
            risk_factors.append("Existing medical conditions")
    
    if len(medications) > 5:
        risk_factors.append("Polypharmacy (>5 medications)")
    
    return {
        "overall_risk": overall_risk,
        "total_interactions": total_interactions,
        "severity_breakdown": {
            "major": major_count,
            "moderate": moderate_count,
            "minor": minor_count
        },
        "risk_factors": risk_factors,
        "medication_count": len(medications)
    }

def generate_prescription_recommendations(prescription, interactions: List[Dict], risk_assessment: Dict, patient_context: Dict) -> List[str]:
    """Generate recommendations for a specific prescription."""
    recommendations = []
    
    # Base recommendations on risk level
    risk_level = risk_assessment.get('overall_risk', 'minimal')
    
    if risk_level == "high":
        recommendations.append("🚨 URGENT: Contact prescribing physician immediately")
        recommendations.append("Consider alternative medications or dosage modifications")
        recommendations.append("Implement enhanced monitoring protocols")
    elif risk_level == "moderate":
        recommendations.append("⚠️ CAUTION: Schedule medical review within 24-48 hours")
        recommendations.append("Monitor patient for interaction symptoms")
        recommendations.append("Consider dose timing adjustments")
    elif risk_level == "low":
        recommendations.append("ℹ️ AWARENESS: Standard monitoring protocols apply")
        recommendations.append("Educate patient about potential interactions")
    
    # Add patient-specific recommendations
    if patient_context:
        if patient_context.get('age', 0) > 65:
            recommendations.append("👴 ELDERLY PATIENT: Use enhanced monitoring due to age")
        
        if 'kidney' in str(patient_context.get('medical_conditions', '')).lower():
            recommendations.append("🔍 RENAL CONSIDERATION: Monitor kidney function")
        
        if 'liver' in str(patient_context.get('medical_conditions', '')).lower():
            recommendations.append("🔍 HEPATIC CONSIDERATION: Monitor liver function")
    
    # Add interaction-specific recommendations
    major_interactions = [i for i in interactions if i.get('severity') == 'major']
    if major_interactions:
        recommendations.append("📋 DOCUMENTATION: Document interaction assessment in patient record")
        recommendations.append("🤝 COORDINATION: Ensure all healthcare providers are aware")
    
    return recommendations