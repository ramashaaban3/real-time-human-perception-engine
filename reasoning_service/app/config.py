import os


# Sistem modu
# rules -> sadece kurallar
# llm   -> LLM kullan, hata olursa fallback
# auto  -> LLM katmanı aktif, ama kurallar çekirdek mantık olarak durur
MODE = os.getenv("MODE", "rules").strip().lower()


# OpenAI API anahtarı
# Environment variable üzerinden okunur
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


# Kullanılacak model adı
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# API çağrısı için timeout süresi
OPENAI_TIMEOUT_SEC = float(os.getenv("OPENAI_TIMEOUT_SEC", "15"))

USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"