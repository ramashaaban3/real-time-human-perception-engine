# deque: sabit uzunlukta bir liste yapısı sağlar
# örneğin maxlen=5 ise en eski eleman otomatik silinir
from collections import deque

# time: zaman ölçmek için kullanacağız
import time


# ReasoningState sınıfı
# Bu sınıf sistemin "hafızasını" tutar
# Çünkü reasoning kararları sadece tek frame'e göre verilmez
class ReasoningState:

    # constructor (sınıf oluşturulurken çalışır)
    def __init__(self, buffer_size: int = 5):

        # Son N detection sonucunu tutacak buffer
        # örnek: [True, True, False, True, False]
        self.detection_buffer = deque(maxlen=buffer_size)

        # En son action üretildiği zaman
        # cooldown hesaplamak için kullanılır
        self.last_trigger_time = 0.0

    # Yeni detection sonucunu buffer'a ekler
    # detected True ise "insan var" demektir
    def add_detection(self, detected: bool):

        # detection sonucu buffer'a eklenir
        self.detection_buffer.append(detected)

    # Detection stabil mi kontrol eder
    # kural: son 5 frame içinde en az 3 True varsa stabil kabul edilir
    def is_stable(self):

        # True değerleri sayılır
        # True python'da 1 olarak sayılır
        return sum(self.detection_buffer) >= 3

    # Cooldown aktif mi kontrol eder
    def cooldown_active(self, cooldown_sec: float):

        # Şu anki zaman
        current_time = time.time()

        # Son trigger'dan sonra geçen süre
        elapsed = current_time - self.last_trigger_time

        # Eğer cooldown süresi dolmadıysa
        if elapsed < cooldown_sec:

            # cooldown aktif
            # kalan süre hesaplanır
            remaining = cooldown_sec - elapsed

            return True, round(remaining, 2)

        # cooldown bitmiş
        return False, 0.0

    # Bir action tetiklendiğinde çağrılır
    def mark_triggered(self):

        # trigger zamanı güncellenir
        self.last_trigger_time = time.time()

    # Sistemi resetlemek için
    # test ederken kullanışlıdır
    def reset(self):

        # detection buffer temizlenir
        self.detection_buffer.clear()

        # trigger zamanı sıfırlanır
        self.last_trigger_time = 0.0
