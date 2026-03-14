# FastAPI framework
from fastapi import FastAPI

# Perception'dan gelen veri modeli
# Decision sonucu modeli
from shared.schemas import PerceptionResult, DecisionResult

# Sistem state sınıfı
from app.state import ReasoningState


# FastAPI uygulaması oluşturulur
app = FastAPI(title="Reasoning Service")


# Reasoning state nesnesi oluşturulur
# buffer_size = son kaç frame tutulacak
state = ReasoningState(buffer_size=5)


# Cooldown süresi (saniye)
COOLDOWN_SEC = 10.0


# Health check endpoint
# Servisin çalışıp çalışmadığını kontrol etmek için
@app.get("/health")
def health():

    return {"status": "ok"}


# Sistemi resetlemek için endpoint
# test sırasında çok faydalıdır
@app.post("/v1/reasoning/reset")
def reset():

    # state temizlenir
    state.reset()

    return {"status": "reset_ok"}


# Ana karar endpoint'i
@app.post("/v1/reasoning/decide", response_model=DecisionResult)
def decide(payload: PerceptionResult):

    # Perception sonucundan detection bilgisi alınır
    detected = payload.primary_person.detected

    # detection sonucu state buffer'a eklenir
    state.add_detection(detected)

    # stabil detection kontrol edilir
    stable_detection = state.is_stable()

    # cooldown kontrol edilir
    cooldown_active, cooldown_remaining = state.cooldown_active(COOLDOWN_SEC)

    # varsayılan karar
    action = "NO_ACTION"
    reason = "No rule matched."

    # Kural 1
    # Birden fazla kişi varsa
    if payload.people_count > 1:

        action = "MULTI_PERSON_WARN"
        reason = "Multiple people detected."

    # Kural 2
    # Detection stabil değilse
    elif not stable_detection:

        action = "NO_ACTION"
        reason = "Detection not stable yet."

    # Kural 3
    # Cooldown aktifse
    elif cooldown_active:

        action = "NO_ACTION"
        reason = "Cooldown active."

    # Kural 4
    # Stabil detection ve kişi ortadaysa
    elif payload.primary_person.position == "center":

        action = "GREET"
        reason = "Stable person detected at center."

        # cooldown başlatılır
        state.mark_triggered()

    # Kural 5
    # Stabil detection ve kişi solda veya sağdaysa
    elif payload.primary_person.position in ["left", "right"]:

        action = "ALIGN_REQUEST"

        reason = f"Person detected at {payload.primary_person.position}."

        # cooldown başlatılır
        state.mark_triggered()

    # DecisionResult modeli döndürülür
    return DecisionResult(
        # alınan karar
        action=action,
        # kararın sebebi
        reason=reason,
        # detection stabil mi
        stable_detection=stable_detection,
        # cooldown aktif mi
        cooldown_active=cooldown_active,
        # kalan cooldown süresi
        cooldown_remaining_sec=cooldown_remaining,
    )
