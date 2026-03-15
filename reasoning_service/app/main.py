# FastAPI framework
from fastapi import FastAPI

# Perception sonucu ve decision sonucu şemaları
from shared.schemas import PerceptionResult, DecisionResult

# Reasoning state sınıfı
from app.state import ReasoningState

# Veritabanı başlatma ve kayıt ekleme fonksiyonları
from app.db import init_db, insert_event

# Süre ölçmek için
import time

# Zaman damgası üretmek için
from datetime import datetime


# FastAPI uygulaması oluşturulur
app = FastAPI(title="Reasoning Service")


# Son frame'leri tutan state nesnesi
state = ReasoningState(buffer_size=5)


# Cooldown süresi (saniye)
COOLDOWN_SEC = 10.0


# Uygulama ayağa kalkarken çalışır
@app.on_event("startup")
def on_startup():

    # Veritabanı ve tablo oluşturulur
    init_db()


# Health check endpoint
@app.get("/health")
def health():

    return {"status": "ok"}


# State'i sıfırlamak için endpoint
@app.post("/v1/reasoning/reset")
def reset():

    # Buffer ve trigger zamanı temizlenir
    state.reset()

    return {"status": "reset_ok"}


# Ana reasoning endpoint'i
@app.post("/v1/reasoning/decide", response_model=DecisionResult)
def decide(payload: PerceptionResult):

    # Reasoning işleminin başlangıç zamanı
    start_time = time.perf_counter()


    # Perception sonucundan "insan var mı" bilgisi alınır
    detected = payload.primary_person.detected


    # Detection sonucu buffer'a eklenir
    state.add_detection(detected)


    # Stabil detection kontrol edilir
    stable_detection = state.is_stable()


    # Cooldown durumu kontrol edilir
    cooldown_active, cooldown_remaining = state.cooldown_active(COOLDOWN_SEC)


    # Varsayılan action
    action = "NO_ACTION"
    reason = "No rule matched."


    # Kural 1: birden fazla kişi varsa
    if payload.people_count > 1:

        action = "MULTI_PERSON_WARN"
        reason = "Multiple people detected."


    # Kural 2: detection henüz stabil değilse
    elif not stable_detection:

        action = "NO_ACTION"
        reason = "Detection not stable yet."


    # Kural 3: cooldown aktifse
    elif cooldown_active:

        action = "NO_ACTION"
        reason = "Cooldown active."


    # Kural 4: kişi ortadaysa ve stabilse
    elif payload.primary_person.position == "center":

        action = "GREET"
        reason = "Stable person detected at center."

        # Action üretildiği için cooldown başlatılır
        state.mark_triggered()


    # Kural 5: kişi solda/sağdaysa ve stabilse
    elif payload.primary_person.position in ["left", "right"]:

        action = "ALIGN_REQUEST"
        reason = f"Person detected at {payload.primary_person.position}."

        # Action üretildiği için cooldown başlatılır
        state.mark_triggered()


    # Reasoning tarafındaki uçtan uca latency ölçülür
    e2e_latency_ms = (time.perf_counter() - start_time) * 1000.0


    # Veritabanına event kaydı eklenir
    insert_event(
        created_at=datetime.utcnow().isoformat(),          # UTC zaman damgası
        people_count=payload.people_count,
        detected=payload.primary_person.detected,
        confidence=payload.primary_person.confidence,
        position=payload.primary_person.position,
        inference_time_ms=payload.inference_time_ms,
        fps=payload.fps,
        action=action,
        reason=reason,
        stable_detection=stable_detection,
        cooldown_active=cooldown_active,
        cooldown_remaining_sec=cooldown_remaining,
        e2e_latency_ms=round(e2e_latency_ms, 2),
    )


    # Decision sonucu döndürülür
    return DecisionResult(
        action=action,
        reason=reason,
        stable_detection=stable_detection,
        cooldown_active=cooldown_active,
        cooldown_remaining_sec=cooldown_remaining,
    )