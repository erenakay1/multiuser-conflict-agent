# Etiketleme Kılavuzu: Talimat Çakışmaları (v1)

<!-- Bu dosya bir ŞABLONDUR. Tablolar ve örnekler koddan/veriden alınmıştır; açıklama metinlerini
     Yusuf yazar (akademik dürüstlük kuralı). Kod tarafındaki karşılık: src/mucon/schemas.py
     `ConflictType`. Bu kılavuz değişirse ConflictType docstring'i de güncellenmeli. -->

**Sorumlu:** Yusuf Daşdemir · **Sürüm:** v1 · **Tarih:** <!-- GG.AA.YYYY -->

## 1. Amaç ve kapsam
<!-- YUSUF YAZACAK: Etiketlemenin amacı (RQ1, dedektörlerin P/R/F1 ölçümü için altın standart),
     neyin etiketlendiği (mesaj çiftleri) ve neyin kapsam dışında olduğu. -->

## 2. Etiketleme birimi
| Öğe | Tanım |
|---|---|
| Birim | Aynı senaryodaki iki **kullanıcı mesajı** (sıra önemsiz) |
| Karar | `has_conflict`: evet / hayır; evetse `conflict_type` (4 türden biri) |
| Kayıt | `data/labels/<etiketleyici>.jsonl`, satır başına bir `ConflictLabel` |
| Varsayılan | Listelenmeyen her çift `has_conflict = false` olarak kaydedilir |

## 3. Çakışmanın tanımı
<!-- YUSUF YAZACAK: Çakışma ölçütünü kendi cümlelerinle yaz. Koddaki işlevsel tanım:
     "iki talimatı aynı anda sağlayan hiçbir etkinlik planı yoktur". -->

## 4. Çakışma türleri

| Tür | Öznitelik | Ölçüt (koddaki işlevsel tanım) | Kullanıcılar |
|---|---|---|---|
| `direct` | Aynı | Kategorik değerler ayrık (eq X ↔ eq Y, eq X ↔ neq X) | Farklı |
| `range` | Aynı, sayısal/sıralı | Aralıklar kesişmiyor (≤ a ↔ ≥ b, a < b) | Farklı |
| `indirect` | Farklı | Ortam kuralı yüzünden birlikte sağlanamıyor | Farklı |
| `revision` | Aynı | Kullanıcı önceki talimatını değiştiriyor | **Aynı** |

### 4.1 `direct`
<!-- YUSUF YAZACAK: tanım + ne zaman direct sayılır -->

| Örnek (sc-0005) | |
|---|---|
| Mesaj A | "I'm only free on Tuesday, Dec 8." |
| Mesaj B | "Let's do it on Friday, Dec 4." |

### 4.2 `range`
<!-- YUSUF YAZACAK -->

| Örnek (sc-0008) | |
|---|---|
| Mesaj A | "I'd rather go somewhere nicer, at least 2300 TL per person." |
| Mesaj B | "My budget is 2000 TL max." |

### 4.3 `indirect`
<!-- YUSUF YAZACAK: Etiketleyici mekan veritabanına bakmaz; aşağıdaki ortam kuralları
     sağduyu bilgisi olarak kabul edilir. -->

Ortam kuralları (`src/mucon/env/event_planning.py`):

| Talimat 1 | Talimat 2 | Neden birlikte sağlanamaz |
|---|---|---|
| Vegan menü | Steakhouse | Steakhouse'larda vegan/vejetaryen seçenek yok |
| Kişi başı ≤ 400 TL | Fine dining | Fine dining kişi başı ≥ 900 TL |
| Tekerlekli sandalye erişimi | Rooftop bar | Rooftop bar'lar erişilebilir değil |
| ≥ 15 kişilik yer | Escape room | Escape room en fazla 8 kişi |

| Örnek (sc-0017) | |
|---|---|
| Mesaj A | "I don't want to spend more than 400 TL per person." |
| Mesaj B | "I vote for a fine-dining restaurant." |

### 4.4 `revision`
<!-- YUSUF YAZACAK: aynı kullanıcı; eski + yeni talimat çifti etiketlenir. -->

| Örnek (sc-0002) | |
|---|---|
| Mesaj A (önce) | "Can we plan it for Saturday, Dec 5?" |
| Mesaj B (sonra, aynı kullanıcı) | "Update from my side: Sunday, Dec 6 works best for me." |

## 5. Çakışma OLMAYAN zor durumlar (near-miss)
<!-- YUSUF YAZACAK: Aynı konudan söz eden ama uyumlu talimatlar neden çakışma değildir. -->

| Mesaj A | Mesaj B | Neden çakışma değil |
|---|---|---|
| "I could do Friday, Dec 4 or Sunday, Dec 13." | "Let's do it on Sunday, Dec 13." | Pazar ikisini de sağlar |
| Bütçe ≤ 600 TL | Bütçe ≤ 900 TL | 600 TL altı ikisini de sağlar |
| Saat ≥ 18:00 | Saat ≤ 20:00 | 18:00–20:00 arası ikisini de sağlar |
| Konum = Kadıköy | Konum ≠ Beşiktaş | Kadıköy ikisini de sağlar |

## 6. Karar kuralları ve sınır durumlar
<!-- YUSUF YAZACAK: madde madde. Etiketleme sırasında karşılaşılan belirsizlikler buraya eklenir
     (kılavuz v2). Örnek sorular:
     - Bir çift birden fazla türe uyuyorsa hangisi seçilir?
     - "Tercih" (soft) ile "zorunluluk" (hard) arasındaki fark etiketi değiştirir mi?
     - revision çifti ayrıca başka bir kullanıcıyla da çakışıyorsa? -->

## 7. Etiketleme aracı
**Tarayıcı arayüzü (önerilen):**
```bash
uv run mucon label-ui                              # results/label_ui/index.html açılır
# ... etiketle, "Dışa aktar" → labels_yusuf.json indirilir
uv run mucon import-labels ~/Downloads/labels_yusuf.json   # → data/labels/yusuf.jsonl
```
Mesajlara tıklayarak çift seçilir, tür butonla (veya `d r i v`) verilir; ilerleme tarayıcıda saklanır.

**Terminal alternatifi:**
```bash
uv run mucon label --annotator yusuf --n 50     # kaldığı yerden devam eder, q = çık
```
- Senaryonun mesajları numaralı gösterilir; üretecin etiketleri **gösterilmez**.
- Girdi: `1-3 direct, 2-5 ind` → 1–3 direct, 2–5 indirect. Boş girdi = çakışma yok.
- Tür adı kısaltılabilir: `dir`, `ra`, `ind`, `rev`. Not eklemek için: `1-3 dir # emin değilim`.

Uyum ölçümü:
```bash
uv run mucon agreement yusuf generator   # insan ↔ üreteç etiketleri
uv run mucon agreement yusuf eren        # etiketleyiciler arası (Cohen's κ)
```

## 8. Sürüm geçmişi
| Sürüm | Tarih | Değişiklik |
|---|---|---|
| v1 | <!-- tarih --> | İlk sürüm |
