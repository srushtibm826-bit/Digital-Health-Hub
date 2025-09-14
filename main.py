import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import requests
import base64
import os
import pandas as pd
import io
from PIL import Image
import pytesseract
import difflib
import re
from PIL import ImageEnhance

# Set the path to the Tesseract executable
# NOTE: YOU MUST UPDATE THIS PATH TO MATCH YOUR INSTALLATION
# For Windows:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For macOS/Linux, try this if Tesseract is in your PATH:
# pytesseract.pytesseract.tesseract_cmd = 'tesseract'

app = FastAPI(
    title="Drug Interaction and Dosage API",
    description="An API to analyze drug interactions, provide dosage recommendations, extract drug info, and describe images."
)

# ===== DRUG DATA =====
DRUG_DATA = {
    "ibuprofen": {
        "alternatives": ["naproxen", "acetaminophen"],
        "interactions": ["warfarin", "aspirin"],
        "dosages": {
            "child": "10 mg/kg every 6-8 hours",
            "adult": "200-400 mg every 4-6 hours",
            "elderly": "200 mg every 6 hours (with caution)"
        }
    },
    "dolo 650": {
        "alternatives": ["Crocin 650 mg", "Dolopar 650 mg"],
        "interactions": [
            "chloramphenicol", "lamotrigine", "aspirin",
            "anticonvulsants", "liver disease", "Gilbert’s syndrome"
        ],
        "dosages": {
            "child": "Not recommended under 12 years",
            "adult": "650 mg (1 tablet) every 4-6 hours as needed; maximum 4 doses daily",
            "elderly": "Use with caution—likely same dosing with medical supervision"
        }
    },
    "eldoper": {
        "alternatives": ["Imodium 2 mg", "Loopra 2 mg"],
        "interactions": ["Alcohol", "Domperidone", "acute ulcerative colitis", "dysentery", "pseudomembranous colitis"],
        "dosages": {
            "child": {
                "2–5 years": "approx. 3 mg/day (~1.5 capsules)",
                "6–8 years": "approx. 4 mg/day (2 capsules)",
                "8–12 years": "approx. 6 mg/day (3 capsules)",
                "under 2 years": "Not recommended"
            },
            "adult": "4 mg after first loose stool, then 2 mg after each unformed stool; max 16 mg/day; stop within 48 hours for acute cases",
            "elderly": "Same as adult, with medical supervision"
        }
    },
    "b complex": {
        "alternatives": ["Becozyme C Forte", "Neurobion Forte", "Becosules"],
        "interactions": ["Levodopa", "Chloramphenicol", "Alcohol (excessive use)"],
        "dosages": {
            "child": "As directed by physician; typical dose 1 capsule/tablet daily",
            "adult": "1 capsule/tablet daily or as prescribed",
            "elderly": "Same as adult dose; monitor for absorption issues"
        }
    },
    "telmikind 80": {
        "alternatives": ["Micardis 80 mg", "Telma 80 mg"],
        "interactions": ["Alcohol", "Potassium supplements or potassium-sparing diuretics", "Insulin and other antidiabetic medications"],
        "dosages": {
            "child": "Not recommended under 18 years",
            "adult": "Typical antihypertensive dose: 80 mg once daily; can also be used at lower doses (20–40 mg) depending on response",
            "elderly": "Same as adult, with medical supervision; monitor kidney function, BP, and potassium levels"
        }
    },
    "warfarin": {
        "alternatives": ["dabigatran", "rivaroxaban"],
        "interactions": ["ibuprofen", "aspirin", "omeprazole"],
        "dosages": {
            "child": "Initial dose based on age/weight; requires strict monitoring",
            "adult": "2-5 mg per day, adjusted based on INR",
            "elderly": "Lower initial dose; requires strict monitoring"
        }
    },
    "Lidocam": {
    "alternatives": ["bupivacaine", "prilocaine", "ropivacaine"],
    "interactions": [
        "amiodarone",
        "beta-blockers",
        "phenytoin",
        "quinidine",
        "cimetidine"
    ],
    "dosages": {
        "child": "Dose depends on age/weight; typically 1–1.5 mg/kg (not exceeding 3–4 mg/kg without epinephrine)",
        "adult": "Topical: apply thin layer 2–3 times daily; Injection: 1–5 mg/kg depending on route (max 300 mg without epinephrine, 500 mg with epinephrine)",
        "elderly": "Use lowest effective dose due to reduced metabolism and higher risk of toxicity"
    }
},

    "Dapacrine M 10":{
        "alternatives": ["Xigduo XR", "Glucreta M", "Dapanorm M", "Udapa-M 500 XR"],
        "interactions": ["diuretics", "alcohol"],
        "dosages": {
            "child": "Not recommended for patients <18 years of age",
            "adult": "Typically once daily, usually in the morning with or without food (often with meals), as prescribed; dosage and duration individualized",
            "elderly": "Not recommended for patients 85 years or older"
        }
    },
    "omeprazole": {
        "alternatives": ["esomeprazole", "pantoprazole"],
        "interactions": ["warfarin", "diazepam"],
        "dosages": {
            "child": "10-20 mg once daily",
            "adult": "20-40 mg once daily",
            "elderly": "20 mg once daily"
        }
    },
    "aspirin": {
        "alternatives": ["ibuprofen", "acetaminophen"],
        "interactions": ["warfarin", "ibuprofen"],
        "dosages": {
            "child": "Not recommended due to Reye's syndrome risk",
            "adult": "325-650 mg every 4 hours",
            "elderly": "75-100 mg once daily (low-dose for cardiovascular protection)"
        }
    }
}

# ===== Normalization Helpers =====
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)  # remove special chars
    text = text.replace("0", "o").replace("1", "l")  # OCR number fixes
    text = text.replace("rg", "mg")  # common OCR mistake
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Fuzzy + tokenized matching
def fuzzy_match(caption, dataset, threshold=0.7):
    caption_norm = normalize_text(caption)
    tokens = caption_norm.split()
    matches = []

    for drug_key in dataset.keys():
        drug_norm = normalize_text(drug_key)

        # Direct substring match
        if drug_norm in caption_norm:
            matches.append(drug_key)
            continue

        # Token fuzzy match
        for token in tokens:
            score = difflib.SequenceMatcher(None, drug_norm, token).ratio()
            if score >= threshold:
                matches.append(drug_key)
                break
    return list(set(matches))  # remove duplicates

# Ranking fallback
def rank_matches(caption, dataset, top_n=3):
    caption_norm = normalize_text(caption)
    scores = []
    for drug_key in dataset.keys():
        drug_norm = normalize_text(drug_key)
        score = difflib.SequenceMatcher(None, drug_norm, caption_norm).ratio()
        scores.append((drug_key, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

# ===== Pydantic Models =====
class DrugInteractionRequest(BaseModel):
    drugs: List[str]

class DosageRequest(BaseModel):
    drug: str
    age: int

class AlternativeRequest(BaseModel):
    drug: str

class NlpRequest(BaseModel):
    text: str

# ===== Helper =====
def get_age_category(age: int) -> str:
    if age < 18:
        return "child"
    elif age >= 65:
        return "elderly"
    else:
        return "adult"

# ===== API Endpoints =====
@app.post("/check_interactions")
def check_interactions(request: DrugInteractionRequest):
    interactions = []
    drug_keys = [find_drug_key(d) for d in request.drugs if find_drug_key(d)]

    for i, drug1 in enumerate(drug_keys):
        for drug2 in drug_keys[i+1:]:
            if drug2 in DRUG_DATA[drug1]["interactions"]:
                interactions.append(f"Harmful interaction between {drug1} and {drug2}.")

    if not interactions:
        return {"status": "success", "message": "No harmful interactions detected."}
    else:
        return {"status": "warning", "interactions": interactions}

@app.post("/recommend_dosage")
def recommend_dosage(request: DosageRequest):
    drug_key = find_drug_key(request.drug)
    age_category = get_age_category(request.age)

    if drug_key:
        dosage = DRUG_DATA[drug_key]["dosages"].get(age_category, "Dosage information not available for this age group.")
        return {"drug": drug_key, "age_category": age_category, "recommendation": dosage}
    else:
        return {"drug": request.drug, "recommendation": "Drug not found in database."}

@app.post("/suggest_alternatives")
def suggest_alternatives(request: AlternativeRequest):
    drug_key = find_drug_key(request.drug)
    if drug_key:
        alternatives = DRUG_DATA[drug_key].get("alternatives", [])
        return {"drug": drug_key, "alternatives": alternatives}
    else:
        return {"drug": request.drug, "message": "Drug not found in database."}

def is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """Check similarity between two normalized strings."""
    return difflib.SequenceMatcher(None, a, b).ratio() >= threshold

@app.post("/extract_info")
def extract_info(request: NlpRequest):
    try:
        text = request.text
        norm_text = normalize_text(text)
        found_drugs = []

        for drug_key in DRUG_DATA.keys():
            drug_norm = normalize_text(drug_key)

            # ✅ check if drug name is present in text
            if drug_norm in norm_text or is_similar(drug_norm, norm_text, threshold=0.7):
                found_drugs.append({
                    "drug": drug_key,
                    "alternatives": DRUG_DATA[drug_key].get("alternatives", []),
                    "interactions": DRUG_DATA[drug_key].get("interactions", []),
                    "dosages": DRUG_DATA[drug_key].get("dosages", {})
                })

        if found_drugs:
            return {"status": "success", "input": request.text, "matches": found_drugs}
        else:
            return {"status": "no_match", "input": request.text, "message": "No matching drugs found in dataset."}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/image_to_text")
async def image_to_text(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        # Open image in grayscale
        image = Image.open(io.BytesIO(contents)).convert("L")

        # Improve contrast instead of hard threshold
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)

        # OCR extraction
        raw_text = pytesseract.image_to_string(image, lang="eng")
        caption = raw_text.strip()

        # Try to match with dataset
        matches = fuzzy_match(caption, DRUG_DATA)

        response_data = {
            "status": "success" if matches else "no_match",
            "caption_raw": raw_text.splitlines(),
            "caption_joined": caption,
            "caption_normalized": normalize_text(caption),
            "matches": []
        }

        if matches:
            for m in matches:
                response_data["matches"].append({
                    "drug": m,
                    "alternatives": DRUG_DATA[m].get("alternatives", []),
                    "interactions": DRUG_DATA[m].get("interactions", []),
                    "dosages": DRUG_DATA[m].get("dosages", {})
                })
        else:
            response_data["suggestions"] = rank_matches(caption, DRUG_DATA)
            response_data["message"] = "No matching drugs found. Suggestions provided based on similarity."

        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)})
    

# ===== Helper: Find drug key by fuzzy matching =====
def find_drug_key(name: str):
    norm_name = normalize_text(name)
    for drug in DRUG_DATA.keys():
        if is_similar(normalize_text(drug), norm_name, threshold=0.75):
            return drug
    return None

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)