# 0002 — H3 sonrası tasarım kararları

- **Tarih:** 2026-11-16
- **Durum:** Kabul edildi (1, 2), Bekliyor (3)
- **Karar verenler:** Eren Akay, Yusuf Daşdemir

## 1. S2 (yetki hiyerarşisi): eşit yetkide kullanıcılara sor
Harness-MU'da eşit yetki için eşitlik bozma kuralı yok (`mediator.py`: `auth >= max_auth` olan
herkes "follow" alır; çakışma çözülmeden kalır). S2'de en yüksek `rank`'teki kullanıcıların
kısıtları çakışırsa strateji `ActionType.ASK_CLARIFICATION` döndürür. Bu, Harness-MU'ya değil
bize ait bir eklentidir ve raporda öyle belirtilir.

## 2. Öneri cümleleri yumuşak (soft) kısıttır
"How about X?" / "I vote for X" biçimindeki öneriler `Strength.SOFT` olarak üretilir ve
çıkarılır. Gerekçe: etiketleyici notu (sc-0010) ve kısıt çıkarıcının bu mesajları kısıt
saymaması. Çakışma etiketleri değişmez (çakışma tanımı güçten bağımsız: ikisini birden sağlayan
plan yok); değişen, görev başarısı ve memnuniyet hesabıdır.
Uygulama: H4, senaryo üreteci v1 (`sim/templates.py` + `sim/scenario_generator.py`).

## 3. Deney modeli (DeepInfra) — bekliyor
Geliştirme Ollama (`DEV_MODEL`) ile sürüyor. Raporlanacak deneyler için DeepInfra üzerinden bir
model kullanılacak; model seçimi H4'te yapılacak, ardından `LLMClient`'a sağlayıcı eklenecek.
