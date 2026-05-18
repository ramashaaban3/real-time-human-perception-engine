# JSON parse etmek için
import json

# OpenAI istemcisi
from openai import OpenAI

# Config değerleri
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT_SEC

# Ortak şemalar
from shared.schemas import PerceptionResult, DecisionResult


# Rules sonucu için hazır Türkçe cümle üretir
# Bu fallback durumunda kullanılır
def build_rule_based_utterance(rule_result: DecisionResult) -> str:

    if rule_result.action == "GREET":
        return "Merhaba, hoş geldiniz."

    elif rule_result.action == "ALIGN_REQUEST":
        return "Lütfen biraz ortaya gelir misiniz?"

    elif rule_result.action == "MULTI_PERSON_WARN":
        return "Aynı anda birden fazla kişi algılandı."

    return "Şu anda bir işlem yapılmayacak."


# OpenAI API çağrısı yapan fonksiyon
def call_llm(payload: PerceptionResult, rule_result: DecisionResult) -> dict:

    # API key yoksa hata ver
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    # OpenAI client oluştur
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=OPENAI_TIMEOUT_SEC,
    )

    # Model çıktısını zorlamak için JSON schema
    schema = {
        "name": "robot_decision_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "GREET",
                        "ALIGN_REQUEST",
                        "MULTI_PERSON_WARN",
                        "NO_ACTION",
                    ],
                },
                "utterance_tr": {"type": "string"},
                "certainty": {"type": "number"},
            },
            "required": ["action", "utterance_tr", "certainty"],
            "additionalProperties": False,
        },
    }

    # Sistem talimatı
    system_prompt = """
Sen bir insan-robot etkileşim sisteminin karar katmanısın.
Sana perception ve rules çıktısı verilecek.
Her zaman yalnızca geçerli JSON şemasına uygun cevap ver.
Türkçe kısa ve doğal utterance üret.
Action, mümkünse rules sonucuyla uyumlu olsun.
"""

    # Kullanıcı içeriği
    user_prompt = f"""
Perception sonucu:
- people_count: {payload.people_count}
- detected: {payload.primary_person.detected}
- confidence: {payload.primary_person.confidence}
- position: {payload.primary_person.position}
- inference_time_ms: {payload.inference_time_ms}
- fps: {payload.fps}

Rules sonucu:
- action: {rule_result.action}
- reason: {rule_result.reason}
- stable_detection: {rule_result.stable_detection}
- cooldown_active: {rule_result.cooldown_active}
- cooldown_remaining_sec: {rule_result.cooldown_remaining_sec}

Bu duruma uygun action, utterance_tr ve certainty üret.
"""

    # OpenAI çağrısı
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": schema,
        },
        temperature=0.2,
    )

    # Modelin döndürdüğü içerik
    content = response.choices[0].message.content

    # JSON string -> Python dict
    return json.loads(content)


# LLM + fallback wrapper
def llm_with_fallback(payload: PerceptionResult, rule_result: DecisionResult) -> dict:

    try:
        # Önce LLM dene
        llm_result = call_llm(payload, rule_result)

        return {
            "action": llm_result["action"],
            "utterance_tr": llm_result["utterance_tr"],
            "certainty": float(llm_result["certainty"]),
            "source": "llm",
            "reason": rule_result.reason,
            "stable_detection": rule_result.stable_detection,
            "cooldown_active": rule_result.cooldown_active,
            "cooldown_remaining_sec": rule_result.cooldown_remaining_sec,
        }
    
    except Exception as e:
        print("LLM ERROR:", repr(e))  # 👈 BUNU EKLE

        return {
            "action": rule_result.action,
            "utterance_tr": build_rule_based_utterance(rule_result),
            "certainty": 1.0,
            "source": "llm_fallback_rules",
            "reason": rule_result.reason,
            "stable_detection": rule_result.stable_detection,
            "cooldown_active": rule_result.cooldown_active,
            "cooldown_remaining_sec": rule_result.cooldown_remaining_sec,
        }

def mock_llm(rule_result):
    return {
        "action": rule_result.action,
        "utterance_tr": "Merhaba, sizi algıladım. Hoş geldiniz.",
        "certainty": 0.95,
        "source": "mock_llm",
        "reason": rule_result.reason,
        "stable_detection": rule_result.stable_detection,
        "cooldown_active": rule_result.cooldown_active,
        "cooldown_remaining_sec": rule_result.cooldown_remaining_sec,
    }