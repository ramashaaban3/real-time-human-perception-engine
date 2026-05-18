# FastAPI framework
from fastapi import FastAPI

from app.config import MODE, USE_MOCK_LLM
from app.llm import llm_with_fallback, mock_llm

# CSV export için
from fastapi.responses import FileResponse

# Ortak veri modelleri
from shared.schemas import (
    PerceptionResult,
    DecisionResult,
    EventRecord,
    LLMDecisionResult,
)

# Sistem state sınıfı
from app.state import ReasoningState

# DB fonksiyonları
from app.db import (
    init_db,
    insert_event,
    get_all_events,
    get_latest_event,
    export_events_to_csv,
)

# Rule motoru
from app.rules import run_rules

# LLM fonksiyonları
from app.llm import llm_with_fallback, build_rule_based_utterance

# Config
from app.config import MODE

# Süre ölçmek için
import time

# Zaman damgası için
from datetime import datetime

# Dosya yolu için
from pathlib import Path


# FastAPI uygulaması
app = FastAPI(title="Reasoning Service")


# Son frame'leri tutan state nesnesi
state = ReasoningState(buffer_size=5)


# Uygulama başlangıcında DB oluştur
@app.on_event("startup")
def on_startup():

    init_db()


# Health endpoint
@app.get("/health")
def health():

    return {
        "status": "ok",
        "mode": MODE,
    }


# State reset endpoint
@app.post("/v1/reasoning/reset")
def reset():

    state.reset()

    return {"status": "reset_ok"}


# Eski deterministic endpoint
# Bu endpoint her zaman saf rules çalıştırır
@app.post("/v1/reasoning/decide", response_model=DecisionResult)
def decide(payload: PerceptionResult):

    # reasoning başlangıç zamanı
    start_time = time.perf_counter()

    # rules motorunu çalıştır
    rule_result = run_rules(payload, state)

    # reasoning latency ölç
    e2e_latency_ms = (time.perf_counter() - start_time) * 1000.0

    # veritabanına kaydet
    insert_event(
        created_at=datetime.utcnow().isoformat(),
        people_count=payload.people_count,
        detected=payload.primary_person.detected,
        confidence=payload.primary_person.confidence,
        position=payload.primary_person.position,
        inference_time_ms=payload.inference_time_ms,
        fps=payload.fps,
        action=rule_result.action,
        reason=rule_result.reason,
        stable_detection=rule_result.stable_detection,
        cooldown_active=rule_result.cooldown_active,
        cooldown_remaining_sec=rule_result.cooldown_remaining_sec,
        e2e_latency_ms=round(e2e_latency_ms, 2),
    )

    return rule_result


# Yeni endpoint
# MODE değerine göre rules veya llm çalıştırır
@app.post("/v1/reasoning/decide-llm", response_model=LLMDecisionResult)
def decide_llm(payload: PerceptionResult):

    # reasoning başlangıç zamanı
    start_time = time.perf_counter()

    # Önce her durumda rules sonucu üretilir
    # Bu güvenli çekirdektir
    rule_result = run_rules(payload, state)

    # MODE=rules ise LLM çağırma
    if MODE == "rules":

        result = {
            "action": rule_result.action,
            "utterance_tr": build_rule_based_utterance(rule_result),
            "certainty": 1.0,
            "source": "rules",
            "reason": rule_result.reason,
            "stable_detection": rule_result.stable_detection,
            "cooldown_active": rule_result.cooldown_active,
            "cooldown_remaining_sec": rule_result.cooldown_remaining_sec,
        }

    # MODE=llm veya MODE=auto ise
    elif MODE in ("llm", "auto"):

        if USE_MOCK_LLM:
            result = mock_llm(rule_result)
        else:
            result = llm_with_fallback(payload, rule_result)

    # Geçersiz mod gelirse güvenli fallback
    else:

        result = {
            "action": rule_result.action,
            "utterance_tr": build_rule_based_utterance(rule_result),
            "certainty": 1.0,
            "source": "rules_invalid_mode_fallback",
            "reason": rule_result.reason,
            "stable_detection": rule_result.stable_detection,
            "cooldown_active": rule_result.cooldown_active,
            "cooldown_remaining_sec": rule_result.cooldown_remaining_sec,
        }

    # reasoning latency ölç
    e2e_latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Veritabanına sonucu kaydet
    insert_event(
        created_at=datetime.utcnow().isoformat(),
        people_count=payload.people_count,
        detected=payload.primary_person.detected,
        confidence=payload.primary_person.confidence,
        position=payload.primary_person.position,
        inference_time_ms=payload.inference_time_ms,
        fps=payload.fps,
        action=result["action"],
        reason=result.get("reason", ""),
        stable_detection=bool(result.get("stable_detection", False)),
        cooldown_active=bool(result.get("cooldown_active", False)),
        cooldown_remaining_sec=float(result.get("cooldown_remaining_sec", 0.0)),
        e2e_latency_ms=round(e2e_latency_ms, 2),
    )

    # response modeline dönüştürüp döndür
    return LLMDecisionResult(**result)


# Son kayıtları listeleyen endpoint
@app.get("/v1/reasoning/events", response_model=list[EventRecord])
def list_events(limit: int = 100):

    rows = get_all_events(limit=limit)

    return [
        EventRecord(
            id=row["id"],
            created_at=row["created_at"],
            people_count=row["people_count"],
            detected=bool(row["detected"]),
            confidence=row["confidence"],
            position=row["position"],
            inference_time_ms=row["inference_time_ms"],
            fps=row["fps"],
            action=row["action"],
            reason=row["reason"],
            stable_detection=bool(row["stable_detection"]),
            cooldown_active=bool(row["cooldown_active"]),
            cooldown_remaining_sec=row["cooldown_remaining_sec"],
            e2e_latency_ms=row["e2e_latency_ms"],
        )
        for row in rows
    ]


# Son kaydı getirir
@app.get("/v1/reasoning/events/latest", response_model=EventRecord | None)
def latest_event():

    row = get_latest_event()

    if row is None:
        return None

    return EventRecord(
        id=row["id"],
        created_at=row["created_at"],
        people_count=row["people_count"],
        detected=bool(row["detected"]),
        confidence=row["confidence"],
        position=row["position"],
        inference_time_ms=row["inference_time_ms"],
        fps=row["fps"],
        action=row["action"],
        reason=row["reason"],
        stable_detection=bool(row["stable_detection"]),
        cooldown_active=bool(row["cooldown_active"]),
        cooldown_remaining_sec=row["cooldown_remaining_sec"],
        e2e_latency_ms=row["e2e_latency_ms"],
    )


# CSV export endpoint
@app.get("/v1/reasoning/events/export/csv")
def export_events_csv():

    csv_path = Path("app/events_export.csv")

    export_events_to_csv(str(csv_path))

    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename="events_export.csv",
    )
