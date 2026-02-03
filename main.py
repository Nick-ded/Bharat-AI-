from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import re
import json
from dotenv import load_dotenv

# -------------------------------
# Load API Key
# -------------------------------
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment")

genai.configure(api_key=API_KEY)
app = FastAPI()
# -------------------------------
# Helpers
# -------------------------------
def safe_parse(text: str):
    """
    Safely parse JSON returned by Gemini.
    Prevents API breakage if model returns invalid JSON.
    """
    try:
        return json.loads(text)
    except Exception:
        return {
            "raw": text,
            "error": "Model did not return valid JSON"
        }
# -------------------------------
# Request Body
# -------------------------------
class MessageRequest(BaseModel):
    message: str
# -------------------------------
# Scam Detection Endpoint
# -------------------------------
@app.post("/detect")
def detect_scam(req: MessageRequest):
    prompt = f"""
You are a scam detection system.
Classify this message as:
- scam
- safe
Return ONLY JSON like:
{{
  "classification": "...",
  "confidence": 0.0,
  "reason": "..."
}}
Message: {req.message}
"""
    try:
        response = genai.GenerativeModel(
            "gemini-1.5-flash"
        ).generate_content(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "result": safe_parse(response.text)
    }# -------------------------------
# Honeypot Engagement Endpoint
# -------------------------------
@app.post("/engage")
def engage_scammer(req: MessageRequest):
    prompt = f"""
You are an AI honeypot agent.
A scammer is talking to you.
You must act like a real victim.
Try to extract:
- UPI ID
- bank account number
- phishing links
Reply naturally.
Return ONLY JSON:
{{
  "reply": "...",
  "extracted": {{
    "upi": "...",
    "account": "...",
    "link": "..."
  }}
}}
Message: {req.message}
"""
    try:
        response = genai.GenerativeModel(
            "gemini-1.5-flash"
        ).generate_content(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Regex Extraction (deterministic backup)
    upi = re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", req.message)
    link = re.findall(r"https?://\S+", req.message)
    bank = re.findall(r"\b\d{9,18}\b", req.message)
    return {
        "ai_response": safe_parse(response.text),
        "regex_extracted": {
            "upi": upi[0] if upi else None,
            "link": link[0] if link else None,
            "bank_account": bank[0] if bank else None
        }
    }
# -------------------------------
# Health Check
# -------------------------------
@app.get("/")
def health():
    return {"status": "ok"}
