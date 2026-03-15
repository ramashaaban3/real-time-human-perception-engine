# sqlite3: Python'ın yerleşik SQLite kütüphanesi
import sqlite3

# Path: dosya yolu yönetimini daha temiz yapar
from pathlib import Path


# Veritabanı dosyasının yolu
# app/events.db dosyası oluşturulacak
DB_PATH = Path("app/events.db")


# Veritabanına bağlantı açan fonksiyon
def get_connection():

    # SQLite bağlantısı oluşturulur
    conn = sqlite3.connect(DB_PATH)

    # Satırlara hem index ile hem kolon adıyla erişebilmek için
    conn.row_factory = sqlite3.Row

    return conn


# Veritabanı ve tabloyu ilk kez oluşturur
def init_db():

    # Bağlantı açılır
    conn = get_connection()

    # SQL komutları çalıştırmak için cursor oluşturulur
    cursor = conn.cursor()

    # events tablosu yoksa oluşturulur
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        people_count INTEGER NOT NULL,
        detected INTEGER NOT NULL,
        confidence REAL NOT NULL,
        position TEXT,
        inference_time_ms REAL NOT NULL,
        fps REAL NOT NULL,
        action TEXT NOT NULL,
        reason TEXT NOT NULL,
        stable_detection INTEGER NOT NULL,
        cooldown_active INTEGER NOT NULL,
        cooldown_remaining_sec REAL NOT NULL,
        e2e_latency_ms REAL NOT NULL
    )
    """)

    # Değişiklikler kaydedilir
    conn.commit()

    # Bağlantı kapatılır
    conn.close()


# Yeni bir event kaydı ekleyen fonksiyon
def insert_event(
    created_at: str,
    people_count: int,
    detected: bool,
    confidence: float,
    position: str | None,
    inference_time_ms: float,
    fps: float,
    action: str,
    reason: str,
    stable_detection: bool,
    cooldown_active: bool,
    cooldown_remaining_sec: float,
    e2e_latency_ms: float,
):

    # Veritabanı bağlantısı açılır
    conn = get_connection()

    # Cursor oluşturulur
    cursor = conn.cursor()

    # Yeni kayıt eklenir
    cursor.execute("""
    INSERT INTO events (
        created_at,
        people_count,
        detected,
        confidence,
        position,
        inference_time_ms,
        fps,
        action,
        reason,
        stable_detection,
        cooldown_active,
        cooldown_remaining_sec,
        e2e_latency_ms
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        created_at,
        people_count,
        int(detected),              # bool → 0/1
        confidence,
        position,
        inference_time_ms,
        fps,
        action,
        reason,
        int(stable_detection),      # bool → 0/1
        int(cooldown_active),       # bool → 0/1
        cooldown_remaining_sec,
        e2e_latency_ms,
    ))

    # Değişiklikler kaydedilir
    conn.commit()

    # Bağlantı kapatılır
    conn.close()