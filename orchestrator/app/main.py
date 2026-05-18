from fastapi import FastAPI, File, UploadFile, HTTPException
import requests
import time

app = FastAPI(title="Orchestrator Service")


# Servis URL'leri (docker network içinde)
PERCEPTION_URL = "http://perception:8001/v1/perception/frame"
REASONING_URL = "http://reasoning:8002/v1/reasoning/decide-llm"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/pipeline/run")
async def run_pipeline(image: UploadFile = File(...)):

    start_time = time.perf_counter()

    # 1️⃣ IMAGE → PERCEPTION
    try:
        files = {"image": (image.filename, await image.read(), image.content_type)}

        perception_response = requests.post(PERCEPTION_URL, files=files)

        if perception_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Perception service failed")

        perception_data = perception_response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Perception error: {str(e)}")

    # 2️⃣ PERCEPTION → REASONING
    try:
        reasoning_response = requests.post(REASONING_URL, json=perception_data)

        if reasoning_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Reasoning service failed")

        reasoning_data = reasoning_response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning error: {str(e)}")

    # toplam latency
    total_time = (time.perf_counter() - start_time) * 1000.0

    return {
        "perception": perception_data,
        "reasoning": reasoning_data,
        "pipeline_latency_ms": round(total_time, 2),
    }
