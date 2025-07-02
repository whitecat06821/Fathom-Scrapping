import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright
import requests
import json
import os
import uuid

app = FastAPI()

class CallData(BaseModel):
    call_name: str
    call_date: str
    call_link: str

@app.post("/webhook")
async def handle_webhook(data: CallData):
    print(f"▶️ Received: {data.call_name} | {data.call_link}")
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "call_name": data.call_name,
        "call_date": data.call_date,
        "call_link": data.call_link
    }
    os.makedirs("jobs", exist_ok=True)
    job_path = os.path.join("jobs", f"{job_id}.json")
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)
    print(f"📝 Job written: {job_path}")
    return {"status": "job_queued", "job_id": job_id}
