# 0001 — Proje yapısı

- **Tarih:** 2026-11-03
- **Durum:** Kabul edildi

## Bağlam
İki kişilik ekip; çok sayıda strateji × dedektör kombinasyonu deneysel olarak karşılaştırılacak.
Geliştirmede yerel, deneylerde API tabanlı LLM kullanılacak.

## Karar
- Python 3.11+, `uv`, `src/` layout, paket adı `mucon`.
- Tüm veri yapıları `schemas.py` içinde pydantic modelleri olarak tanımlanır.
- Dedektörler (`ConflictDetector`) ve stratejiler (`CoordinationStrategy`) ABC arayüzleri arkasında,
  ad → sınıf kayıt tablolarıyla (`DETECTORS`, `STRATEGIES`) config'ten seçilir.
- LLM erişimi tek `LLMClient` üzerinden; Ollama ve OpenAI aynı OpenAI uyumlu API ile kullanılır.
- `ml` bağımlılıkları (torch vb.) opsiyonel extra; dış benchmark'lar `external/` altında, git dışı.

## Sonuçlar
- Yeni strateji/dedektör eklemek tek dosya + kayıt satırıdır.
- Sağlayıcı değişimi yalnızca `.env` ayarıdır.
- DeBERTa olmadan da tüm paket import edilebilir ve test edilebilir.
