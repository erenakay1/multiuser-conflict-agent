# multiuser-conflict-agent (`mucon`)

Haliç Üniversitesi Yazılım Mühendisliği bitirme projesi — **Eren Akay**, **Yusuf Daşdemir**.

**Konu:** Eşit yetkili kullanıcılara sahip çok kullanıcılı LLM agent'larında talimat çakışmalarının
koordinasyonu. Birden fazla kullanıcı aynı agent'a aynı oturumda talimat verir; talimatlar çelişebilir
(ör. biri "cuma", diğeri "cumartesi" der). Literatür bu çakışmaları yetki hiyerarşisiyle çözer
(Harness-MU, Muses-Bench); bu proje eşit yetkili kullanıcılar için çakışma tespit yöntemlerini ve
koordinasyon stratejilerini karşılaştırır.

| | Soru |
|---|---|
| RQ1 | Çakışmalar otomatik olarak ne kadar doğru tespit edilir? |
| RQ2 | Stratejiler görev başarısı, adalet ve verimlilik açısından nasıl karşılaştırılır? |
| RQ3 | Kullanıcılar hangi stratejide kendini kontrol sahibi ve adil davranılmış hisseder? (GP2) |

**Bileşenler:** grup etkinlik planlama ortamı (mock mekan DB) · LLM tabanlı kısıt çıkarıcı ·
3 dedektör (kural, zero-shot LLM, DeBERTa/NLI) · 5 strateji (S0 naive, S1 son talimat, S2 hiyerarşi,
S3 LLM uzlaştırma, S4 oylama/Borda) · gizli tercihli simüle kullanıcılar · metrikler + Wilcoxon.

> Durum: **iskelet**. Modüller `NotImplementedError` içerir; plan için [ROADMAP.md](ROADMAP.md).

## Kurulum

```bash
uv sync                    # ana bağımlılıklar + dev (pytest, ruff)
uv sync --extra ml         # DeBERTa için transformers/torch/datasets (H6)
cp .env.example .env       # LLM ayarları
bash scripts/setup_external.sh   # Muses-Bench ve Harness-MU → external/
```

Geliştirmede LLM olarak yerel [Ollama](https://ollama.com) kullanılır (`ollama pull llama3.1:8b`).
Deneylerde `.env` içinde `LLM_PROVIDER=openai` yapılır.

## Komutlar

```bash
uv run python -m mucon --help   # generate | detect-eval | run | analyze
uv run pytest
uv run ruff check . && uv run ruff format .
```

## Klasörler

| Klasör | Amaç |
|---|---|
| `configs/` | Varsayılan ayarlar (`default.yaml`) ve deney tanımları (`experiments/`) |
| `data/` | Ham veri, üretilen senaryolar, gold etiketler, işlenmiş veri — şema: [data/README.md](data/README.md) |
| `external/` | Dış benchmark klonları (git dışı) |
| `scripts/` | Kurulum yardımcıları |
| `src/mucon/schemas.py` | Tüm pydantic şemaları — tek doğruluk kaynağı |
| `src/mucon/llm/` | Ollama/OpenAI için tek LLM arayüzü |
| `src/mucon/env/` | Etkinlik planlama ortamı, mock mekan DB, sert kısıt kontrolü |
| `src/mucon/sim/` | Senaryo üreteci ve simüle kullanıcılar |
| `src/mucon/extract/` | Mesajdan kısıt çıkarımı |
| `src/mucon/detect/` | Çakışma dedektörleri |
| `src/mucon/strategies/` | Koordinasyon stratejileri S0–S4 |
| `src/mucon/agent/` | Planlama agent'ı ve araçları |
| `src/mucon/eval/` | Metrikler ve istatistik testleri |
| `src/mucon/runner.py` | Deney döngüsü |
| `experiments/` | RQ1/RQ2 deney giriş noktaları |
| `notebooks/` | Keşif ve analiz defterleri |
| `results/` | Deney çıktıları, `results/<tarih>_<deney>/` (git dışı) |
| `tests/` | pytest testleri |
| `docs/` | Literatür tablosu, haftalık/ara raporlar, karar kayıtları |

## Dış benchmark'lar

- Muses-Bench — <https://github.com/Kordi-AI/Multi-User-LLM-Agent> (Yang et al., 2026)
- Harness-MU — <https://github.com/YuanJrShiuan/Harness-MulUser> (Fan et al., 2026)
