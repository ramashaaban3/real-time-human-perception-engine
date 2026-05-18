# Ortak şemalar
from shared.schemas import PerceptionResult, DecisionResult

# State sınıfı
from app.state import ReasoningState


# Cooldown süresi
COOLDOWN_SEC = 10.0


# Rule motoru
# perception sonucunu alır
# state bilgisini kullanır
# deterministic karar döner
def run_rules(payload: PerceptionResult, state: ReasoningState) -> DecisionResult:

    # primary person gerçekten var mı
    detected = payload.primary_person.detected

    # detection sonucu state buffer'a eklenir
    state.add_detection(detected)

    # son 5 frame'e göre stabil mi?
    stable_detection = state.is_stable()

    # cooldown aktif mi?
    cooldown_active, cooldown_remaining = state.cooldown_active(COOLDOWN_SEC)

    # varsayılan değerler
    action = "NO_ACTION"
    reason = "No rule matched."

    # Kural 1: birden fazla kişi varsa
    if payload.people_count > 1:
        action = "MULTI_PERSON_WARN"
        reason = "Multiple people detected."

    # Kural 2: detection stabil değilse
    elif not stable_detection:
        action = "NO_ACTION"
        reason = "Detection not stable yet."

    # Kural 3: cooldown aktifse
    elif cooldown_active:
        action = "NO_ACTION"
        reason = "Cooldown active."

    # Kural 4: stabil kişi ortadaysa
    elif payload.primary_person.position == "center":
        action = "GREET"
        reason = "Stable person detected at center."

        # greet verildiği için cooldown başlatılır
        state.mark_triggered()

    # Kural 5: stabil kişi solda ya da sağdaysa
    elif payload.primary_person.position in ["left", "right"]:
        action = "ALIGN_REQUEST"
        reason = f"Person detected at {payload.primary_person.position}."

        # align request verildiği için cooldown başlatılır
        state.mark_triggered()

    # Sonuç dönülür
    return DecisionResult(
        action=action,
        reason=reason,
        stable_detection=stable_detection,
        cooldown_active=cooldown_active,
        cooldown_remaining_sec=cooldown_remaining,
    )
