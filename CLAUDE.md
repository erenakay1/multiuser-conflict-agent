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

## Raporlama
Hoca (Dr. Öğr. Üyesi Eyüp Kaan ÜLGEN) her hafta ilerleme raporu istiyor. Not verilirken haftalık
raporlar ve süreç de dikkate alınıyor. İki kişilik ekipte kişiler ayrı not alabildiği için
**kimin ne yaptığı her raporda ayrı yazılır.** Hoca görüşmesi her Salı 16.00–16.30.

Üç teslim türü var:

**1. Ortak takip tablosu (bütün sınıfın kullandığı Google Sheets dosyası).** Grubumuzun numarası: **2**.
Her grup sadece kendi satırlarını doldurur. Tablodaki içerikler İngilizce yazılır. Sekmeler:
- `01 | Proje ve Gruplar`: Grup başına tek satır (bir kez doldurulur).
  Sütunlar: Grup No | Üye 1 - Ad Soyad | Üye 1 - Öğrenci No | Üye 2 - Ad Soyad | Üye 2 - Öğrenci No |
  Üye 3 - Ad Soyad | Üye 3 - Öğrenci No | Proje Başlığı | Proje Kısa Açıklaması |
  Çözülecek Problem / Gerekçe | Özgün Teknik Katkı
- `02 | Literatür`: Makale başına bir satır, en az 5 makale.
  Sütunlar: Grup No | Proje Başlığı | Makale Sıra No | Makale Başlığı | Yazar(lar) | Yıl |
  DOI / Yayın Bağlantısı | Çalışmanın Temel Bulgusu | Projeyle İlişkisi
- `03 | Haftalık Takip`: **Her hafta için bir satır.**
  Sütunlar: Grup No | Hafta No | Hafta Tarihi | Bu Hafta Yapılan Çalışmalar |
  Karşılaşılan Sorunlar | Gelecek Haftanın Planı | İlerleme Durumu
  - Grup No = 2, Hafta No = ROADMAP'teki H numarası, Hafta Tarihi = `GG.AA.YYYY – GG.AA.YYYY`.
  - "Bu Hafta Yapılan Çalışmalar" kısmında Eren ve Yusuf ayrı yazılır.
  - "İlerleme Durumu" tablodaki açılır listeden öğrenci tarafından seçilir.
  - Tabloya öğrenciler elle girer. Claude her raporun sonunda kopyalanmaya hazır bir satır üretir.

**2. Haftalık rapor (yarım–1 sayfa):** `docs/weekly-reports/YYYY-MM-DD_HX.md`. Tarih, haftanın
pazartesisidir. Rapor Salı görüşmesinden önce hazır olur. Gerekirse PDF'e çevrilip mail ile gönderilir.

**3. Ara raporlar (3 adet, tarihleri hoca belirler):** `docs/interim-reports/` altında tutulur.
Final rapor şablonunun (APPENDIX 2) ilgili bölümleri gibi yazılır: Times New Roman 12,
1,5 satır aralığı, APA atıf.

### Hafta sonu akışı
Öğrenci "HX raporunu hazırla" dediğinde:
1. `git log` ile o haftanın commit'lerini **yazara göre** (Eren / Yusuf) grupla.
2. ROADMAP.md'deki o haftanın hedefleriyle karşılaştır ve durum işaretle (✅ / ⚠️ / ❌).
3. `results/` altındaki o haftanın çıktılarını ve `docs/literature/` altına eklenen makaleleri listele.
4. TEMPLATE.md'yi bu **olgusal bilgilerle** doldur: yapılanlar, çıktılar, durum tablosu, gelecek hafta.
5. **Karşılaşılan sorunları öğrenciye kısa madde listesi olarak aktar:** Sorun başına bir satır,
   olgusal, gereksiz detay yok; öğrenci isterse ayrıntılandır. Bu liste ham malzemedir. "Sorunlar ve
   değerlendirme" ile "Hocaya sorular" bölümlerini `<!-- ÖĞRENCİ YAZACAK -->` olarak bırak; o
   metinleri öğrenci kendi cümleleriyle yazar (akademik dürüstlük kuralı).
6. Raporun sonuna `03 | Haftalık Takip` sütunlarına uygun, İngilizce, kopyalanmaya hazır bir
   tablo satırı ekle. "Karşılaşılan Sorunlar" hücresini Claude doldurur: 5. adımdaki listeden
   kısa, olgusal maddeler, hücreye sığacak uzunlukta. "İlerleme Durumu" hücresini öğrenci açılır
   listeden seçer.
7. Yeni bir makale eklendiyse `02 | Literatür` için de satır üret.

## Git
- Özellik başına branch (ör. `feat/h3-scenario-generator`), açıklayıcı commit mesajları.
- Ekipte iki kişi var; commit geçmişi kimin ne yaptığını göstermeli.
- **Commit ve push'u Claude yapmaz; öğrenciler kendisi yapar.** Claude dosyaları düzenler, değişen
  dosyaları ve önerilen commit mesajını bildirir, orada durur.
