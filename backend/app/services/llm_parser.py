from transformers import pipeline
import json

# Lightweight instruction-tuned model that runs on CPU
model_name = "google/flan-t5-base"
llm = pipeline("text2text-generation", model=model_name)

def parse_prescription(text):
    prompt = f"""
You are an expert at reading handwritten prescriptions.

Extract and format the following text into structured JSON.

Input:
{text}

Output:
Format:
{{
  "medicine": "...",
  "dosage": "...",
  "frequency": "...",
  "instructions": "...",
  "duration": "..."
}}
"""
    try:
        result = llm(prompt, max_length=256, do_sample=False)[0]["generated_text"]
        json_text = result.strip().split("\n")[0]  # Get the first JSON block
        return json.loads(json_text)
    except Exception as e:
        return {"error": f"Failed to parse prescription: {str(e)}"}

# Alias for backward compatibility - this fixes the import error
parse_prescription_text = parse_prescription