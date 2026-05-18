import time
import cv2
import requests
from pathlib import Path

ORCHESTRATOR_URL = "http://localhost:8000/v1/pipeline/run"
VIDEO_PATH = "datasets/demo_video.mp4"
FRAME_INTERVAL = 15  # her 15 framede bir istek at
MAX_SAMPLES = 15  # demo çok uzamasın diye üst sınır


def run_demo():
    video_path = Path(VIDEO_PATH)

    if not video_path.exists():
        print(f"Video bulunamadı: {video_path}")
        return

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print("Video açılamadı.")
        return

    print("Demo başladı...")
    frame_index = 0
    processed = 0

    while processed < MAX_SAMPLES:
        ret, frame = cap.read()

        if not ret:
            print("Video bitti.")
            break

        if frame_index % FRAME_INTERVAL == 0:
            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                print(f"[{frame_index}] Frame encode başarısız.")
                frame_index += 1
                continue

            files = {"image": ("frame.jpg", buffer.tobytes(), "image/jpeg")}

            start = time.perf_counter()

            try:
                response = requests.post(ORCHESTRATOR_URL, files=files, timeout=30)
                latency_ms = (time.perf_counter() - start) * 1000.0

                if response.status_code == 200:
                    data = response.json()

                    perception = data.get("perception", {})
                    reasoning = data.get("reasoning", {})

                    people_count = perception.get("people_count")
                    position = perception.get("primary_person", {}).get("position")
                    action = reasoning.get("action")
                    utterance = reasoning.get("utterance_tr")
                    source = reasoning.get("source")
                    reason = reasoning.get("reason")
                    stable_detection = reasoning.get("stable_detection")
                    cooldown_active = reasoning.get("cooldown_active")
                    cooldown_remaining_sec = reasoning.get("cooldown_remaining_sec")

                    print(
                        print(
                            f"[frame={frame_index}] "
                            f"people={people_count} "
                            f"position={position} "
                            f"action={action} "
                            f"source={source} "
                            f"stable={stable_detection} "
                            f"cooldown={cooldown_active} "
                            f"cooldown_left={cooldown_remaining_sec} "
                            f"latency_ms={round(latency_ms, 2)} "
                            f"reason={reason} "
                            f"utterance={utterance}"
)
                    )
                else:
                    print(
                        f"[{frame_index}] Hata: status={response.status_code}, body={response.text}"
                    )

            except Exception as e:
                print(f"[{frame_index}] Pipeline hatası: {e}")

            processed += 1

        frame_index += 1

    cap.release()
    print("Demo tamamlandı.")


if __name__ == "__main__":
    run_demo()
