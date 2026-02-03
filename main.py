from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# Load API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()


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

    response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)

    return {"result": response.text}


# -------------------------------
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

    response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)

    # Regex Extraction
    upi = re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", req.message)
    link = re.findall(r"https?://\S+", req.message)
    bank = re.findall(r"\b\d{9,18}\b", req.message)

    return {
        "ai_response": response.text,
        "regex_extracted": {
            "upi": upi[0] if upi else None,
            "link": link[0] if link else None,
            "bank_account": bank[0] if bank else None
        }
    }
