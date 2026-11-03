# CLAUDE.md — Proje kuralları

## Proje bağlamı
Haliç Üniversitesi Yazılım Mühendisliği bitirme projesi (Eren Akay, Yusuf Daşdemir).
Konu: **eşit yetkili kullanıcılara sahip çok kullanıcılı LLM agent'larında talimat çakışmalarının
koordinasyonu.** Birden fazla kullanıcı aynı agent'a aynı oturumda talimat verir ve talimatlar
çelişebilir (ör. grup etkinlik planlarken biri "cuma", diğeri "cumartesi" der). Literatürde bu
çakışmalar yalnızca yetki hiyerarşisiyle çözülür (Fan et al. 2026, Harness-MU; Yang et al. 2026,
Muses-Bench). Biz eşit yetkili kullanıcılar için çakışma tespit yöntemlerini ve koordinasyon
stratejilerini karşılaştırıyoruz.

- RQ1: Çakışmalar otomatik olarak ne kadar doğru tespit edilir?
- RQ2: Stratejiler görev başarısı, adalet ve verimlilik açısından nasıl karşılaştırılır?
- RQ3: Kullanıcılar hangi stratejide kendini kontrol sahibi ve adil davranılmış hisseder? (GP2)

Bileşenler: etkinlik planlama ortamı (`env/`), kısıt çıkarıcı (`extract/`), dedektörler
(`detect/`: kural, zero-shot LLM, DeBERTa/NLI), stratejiler (`strategies/`: S0 naive, S1 son talimat,
S2 hiyerarşi baseline, S3 LLM uzlaştırma, S4 çoğunluk/Borda), simüle kullanıcılar (`sim/`),
metrikler (`eval/`). Plan: [ROADMAP.md](ROADMAP.md).

## Çalışma şekli
- Her seferinde ROADMAP'teki **tek bir haftanın tek bir işine** odaklan.
- Kod yazmadan önce kısa bir plan öner ve **onay bekle**.
- Küçük ve test edilebilir adımlarla ilerle.

## Kod kuralları
- Tip ipuçları zorunlu.
- `src/mucon/schemas.py` içindeki pydantic şemaları **tek doğruluk kaynağı**; başka yerde paralel veri sınıfı tanımlama.
- LLM çağrıları **her zaman** `src/mucon/llm/client.py` (`LLMClient`) üzerinden yapılır; `openai`'yi doğrudan çağırma.
- Rastgelelik için seed config'ten gelir (`configs/*.yaml`); sabit kodlanmış seed yok.
- Deney sonuçları `results/<YYYY-MM-DD>_<deney>/` altına config kopyasıyla kaydedilir.
- Her yeni modüle test yazılır (`tests/`). `uv run pytest` ve `uv run ruff check .` temiz kalmalı.
- `detect/deberta.py` gibi opsiyonel (`ml`) bağımlılıklar fonksiyon içinde import edilir.

## Maliyet
- Geliştirmede Ollama varsayılan (`LLM_PROVIDER=ollama`).
- API ile toplu koşu başlatmadan önce tahmini çağrı/token sayısını raporla ve **onay iste**.

## Akademik dürüstlük kuralı (önemli)
`docs/` altındaki rapor ve literatür **METİNLERİNİ Claude yazmaz.** Bölümün intihal + yapay zeka raporu
kuralı var. Claude şablon oluşturabilir, tablo ve grafik üretebilir, öğrencilerin yazdığı metni inceleyip
hata gösterebilir; ama rapor düzyazısını öğrenciler yazar.

## Git
- Özellik başına branch (ör. `feat/h3-scenario-generator`), açıklayıcı commit mesajları.
- Ekipte iki kişi var; commit geçmişi kimin ne yaptığını göstermeli.
- Kullanıcı istemedikçe push yapma.
