from app.db.database import SessionLocal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('D:/PROJECTS/IntelliRxPlus/backend/app'), "..", "..")))

import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import Prescription

# Step 1: Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 2: Load data from DB
db: Session = SessionLocal()
prescriptions = db.query(Prescription).all()

texts = []
metadata = []

for p in prescriptions:
    combined_text = p.text_raw or ""
    try:
        structured = eval(p.structured_json) if p.structured_json else {}
    except:
        structured = {}
    structured_text = " ".join([f"{k}: {v}" for k, v in structured.items()])
    full_text = combined_text + " " + structured_text

    texts.append(full_text)
    metadata.append({
        "prescription_id": p.id,
        "patient_id": p.patient_id,
        "created_at": str(p.created_at),
        "snippet": full_text[:200]
    })

# Step 3: Create embeddings
embeddings = model.encode(texts, show_progress_bar=True)

# Step 4: Build FAISS index
dimension = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Step 5: Save index and metadata
os.makedirs("backend/data", exist_ok=True)
faiss.write_index(index, "backend/data/faiss.index")

with open("backend/data/meta.pkl", "wb") as f:
    pickle.dump(metadata, f)

print(f"✅ FAISS index built with {len(texts)} entries.")
