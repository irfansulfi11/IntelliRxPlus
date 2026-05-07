from sentence_transformers import SentenceTransformer, util
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

# Dummy FAISS index setup
dim = 384
faiss_index = faiss.IndexFlatL2(dim)
stored_vectors = []
stored_texts = []

def add_prescription_to_index(text):
    embedding = model.encode([text])[0]
    stored_vectors.append(embedding)
    stored_texts.append(text)
    faiss_index.add(np.array([embedding], dtype="float32"))

def semantic_search_prescriptions(query: str):
    if not stored_vectors:
        return []

    query_vector = model.encode([query])[0]
    D, I = faiss_index.search(np.array([query_vector], dtype="float32"), k=3)
    
    results = []
    for idx in I[0]:
        if idx < len(stored_texts):
            results.append({"text": stored_texts[idx], "score": float(D[0][idx])})
    return results
