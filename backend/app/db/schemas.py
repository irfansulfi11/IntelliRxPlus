from pydantic import BaseModel
from typing import Optional

class PrescriptionInput(BaseModel):
    patient_id: str
    text_raw: str
    structured_json: dict
    image_url: Optional[str]
