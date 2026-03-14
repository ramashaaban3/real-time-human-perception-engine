from fastapi import FastAPI, File, UploadFile, HTTPException
import numpy as np
import cv2
import time
from ultralytics import YOLO

from shared.schemas import PerceptionResult, PrimaryPerson

app = FastAPI(title="Perception Service")

# YOLO modelini uygulama başında bir kez yükle
print("YOLO model loading...")
model = YOLO("yolov8n.pt")
print("YOLO model loaded.")


# COCO dataset class id
PERSON_CLASS_ID = 0


@app.get("/health")
def health():
    return {"status": "ok"}


def compute_position(x_center: float, image_width: int) -> str:
    ratio = x_center / image_width

    if ratio < 1 / 3:
        return "left"
    elif ratio < 2 / 3:
        return "center"
    return "right"


@app.post("/v1/perception/frame", response_model=PerceptionResult)
async def process_frame(image: UploadFile = File(...)):
    start_time = time.perf_counter()

    # Dosya içeriğini oku
    contents = await image.read()

    # Byte verisini numpy array'e çevir
    np_array = np.frombuffer(contents, np.uint8)

    # OpenCV ile görüntüye dönüştür
    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    # Eğer görüntü okunamazsa hata ver
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    height, width = frame.shape[:2]

    # YOLO inference
    results = model(frame, verbose=False)
    result = results[0]

    person_boxes = []

    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())

            if cls_id == PERSON_CLASS_ID:
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                person_boxes.append({"bbox": [x1, y1, x2, y2], "confidence": conf})

    people_count = len(person_boxes)

    if people_count == 0:
        primary_person = PrimaryPerson(detected=False, confidence=0.0, position=None)
    else:
        # En yüksek confidence'lı kişiyi seç
        best_person = max(person_boxes, key=lambda item: item["confidence"])

        x1, y1, x2, y2 = best_person["bbox"]
        x_center = (x1 + x2) / 2.0

        position = compute_position(x_center, width)

        primary_person = PrimaryPerson(
            detected=True,
            confidence=round(best_person["confidence"], 4),
            position=position,
        )

    inference_time_ms = (time.perf_counter() - start_time) * 1000.0
    fps = 1000.0 / inference_time_ms if inference_time_ms > 0 else 0.0

    return PerceptionResult(
        people_count=people_count,
        primary_person=primary_person,
        inference_time_ms=round(inference_time_ms, 2),
        fps=round(fps, 2),
    )
