"""
Drug interactions service module
"""

def check_drug_interactions(medications):
    """
    Check for potential drug interactions between medications
    
    Args:
        medications (list): List of medication names or objects
        
    Returns:
        dict: Dictionary containing interaction warnings and severity levels
    """
    interactions = []
    
    if not medications or len(medications) < 2:
        return {
            "interactions": [],
            "has_interactions": False,
            "total_interactions": 0
        }

    known_interactions = {
        ("warfarin", "aspirin"): {
            "severity": "high",
            "description": "Increased bleeding risk"
        },
        ("metformin", "alcohol"): {
            "severity": "medium", 
            "description": "Risk of lactic acidosis"
        }
    }

    for i in range(len(medications)):
        for j in range(i + 1, len(medications)):
            med1 = str(medications[i]).lower()
            med2 = str(medications[j]).lower()

            pair1 = (med1, med2)
            pair2 = (med2, med1)

            if pair1 in known_interactions:
                info = known_interactions[pair1]
            elif pair2 in known_interactions:
                info = known_interactions[pair2]
            else:
                severity = get_interaction_severity(med1, med2)
                if severity != "none":
                    info = {
                        "severity": severity,
                        "description": f"Potential interaction between {med1} and {med2}"
                    }
                else:
                    continue

            interactions.append({
                "medications": [med1, med2],
                "severity": info["severity"],
                "description": info["description"]
            })

    return {
        "interactions": interactions,
        "has_interactions": len(interactions) > 0,
        "total_interactions": len(interactions)
    }


def get_interaction_severity(med1: str, med2: str) -> str:
    """
    Returns the severity level of interaction between two medications.
    
    Args:
        med1 (str): First medication
        med2 (str): Second medication
        
    Returns:
        str: Severity level ('low', 'medium', 'high', or 'none')
    """
    known_severities = {
        ("warfarin", "aspirin"): "high",
        ("metformin", "alcohol"): "medium",
        ("ibuprofen", "aspirin"): "medium",
        ("paracetamol", "alcohol"): "low"
    }

    key1 = (med1.lower(), med2.lower())
    key2 = (med2.lower(), med1.lower())

    return known_severities.get(key1) or known_severities.get(key2) or "none"


def get_drug_info(drug_name):
    """
    Get basic information about a drug
    
    Args:
        drug_name (str): Name of the drug
        
    Returns:
        dict: Basic drug information
    """
    return {
        "name": drug_name,
        "generic_name": drug_name,
        "drug_class": "Analgesic" if "para" in drug_name.lower() else "Unknown",
        "common_side_effects": ["nausea", "drowsiness"],
        "contraindications": ["liver disease"]
    }


def search_drug_database(drug_name):
    """
    Simulates a drug database search
    
    Args:
        drug_name (str): Name of the drug
        
    Returns:
        dict: Drug profile
    """
    return {
        "name": drug_name,
        "available": True,
        "similar_names": [drug_name.capitalize(), drug_name.lower()],
        "description": f"{drug_name.capitalize()} is commonly used in clinical treatments."
    }


def check_allergies(medications, allergies):
    """
    Check if any medications conflict with known allergies
    
    Args:
        medications (list): List of medications
        allergies (list): List of known allergies
        
    Returns:
        dict: Allergy conflict information
    """
    conflicts = []

    if not allergies:
        return {
            "conflicts": [],
            "has_conflicts": False,
            "total_conflicts": 0
        }

    for medication in medications:
        med_name = str(medication).lower()
        for allergy in allergies:
            allergy_name = str(allergy).lower()

            if allergy_name in med_name or med_name in allergy_name:
                conflicts.append({
                    "medication": med_name,
                    "allergy": allergy_name,
                    "severity": "high",
                    "description": f"Potential allergic reaction to {med_name}"
                })

    return {
        "conflicts": conflicts,
        "has_conflicts": len(conflicts) > 0,
        "total_conflicts": len(conflicts)
    }
def check_contraindications(medications, patient_conditions):
    """
    Check for any contraindications between medications and patient health conditions.
    
    Args:
        medications (list): List of medications.
        patient_conditions (list): List of known patient conditions (e.g., 'asthma', 'diabetes').
    
    Returns:
        dict: Contraindication conflicts and details.
    """
    contraindications = {
        "aspirin": ["asthma", "bleeding_disorder"],
        "metformin": ["kidney_disease"],
        "beta_blockers": ["asthma"]
    }

    conflicts = []

    for med in medications:
        med_name = str(med).lower()
        for condition in patient_conditions:
            cond_name = str(condition).lower()
            if med_name in contraindications:
                if cond_name in contraindications[med_name]:
                    conflicts.append({
                        "medication": med_name,
                        "condition": cond_name,
                        "description": f"{med_name} is contraindicated for patients with {cond_name}."
                    })

    return {
        "contraindications": conflicts,
        "has_contraindications": len(conflicts) > 0,
        "total_contraindications": len(conflicts)
    }
def get_alternative_medications(drug_name):
    """
    Get alternative medications for a given drug.
    
    Args:
        drug_name (str): Name of the drug to find alternatives for.
    
    Returns:
        list: List of alternative medication names.
    """
    alternatives_map = {
        "aspirin": ["acetaminophen", "ibuprofen"],
        "metformin": ["glipizide", "glyburide"],
        "paracetamol": ["ibuprofen", "naproxen"]
    }

    name = drug_name.lower()
    return alternatives_map.get(name, ["No known alternatives"])
