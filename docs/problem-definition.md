# Problemin Formal Tanımı (taslak)

<!-- ŞABLON. Düzyazıyı ve matematiksel tanımları Eren yazar (akademik dürüstlük kuralı).
     Aşağıdaki sembol tablosu yalnızca kodla eşleşmeyi kolaylaştırmak içindir; semboller
     değiştirilebilir. Bu metin 1. ara raporun "Problem Tanımı" bölümüne dönüşecek. -->

**Sorumlu:** Eren Akay

## 1. Ortam ve oturum
<!-- EREN YAZACAK: Kullanıcı kümesi, oturum, mesaj dizisi, eşit yetki varsayımı. -->

## 2. Kısıtlar ve plan uzayı
<!-- EREN YAZACAK: Kısıtın tanımı (öznitelik, operatör, değer, sert/yumuşak), planın tanımı,
     bir planın bir kısıtı sağlaması. -->

## 3. Çakışma
<!-- EREN YAZACAK: İki kısıtın çakışması (ortak sağlayıcı plan yokluğu) ve türler
     (docs/annotation-guideline.md ile tutarlı olmalı). -->

## 4. Koordinasyon stratejisi
<!-- EREN YAZACAK: Stratejiyi oturum durumu + tespit edilen çakışmalardan eyleme bir fonksiyon
     olarak tanımla; S0–S4'ü bu tanımın örnekleri olarak konumla. -->

## 5. Değerlendirme hedefleri
<!-- EREN YAZACAK: RQ1 (tespit: P/R/F1), RQ2 (görev başarısı, adalet, verimlilik). -->

---

## Ek: Sembol ↔ kod eşleşmesi

| Kavram | Önerilen sembol | Kod karşılığı (`src/mucon/`) |
|---|---|---|
| Kullanıcı kümesi | U = {u₁, …, uₙ} | `schemas.User`, `Session.users` |
| Kullanıcı yetkisi | rank(u) (eşit yetkide hepsi 0) | `User.rank` (yalnız S2) |
| Mesaj dizisi | M = (m₁, …, m_T) | `Session.messages`, `Message.turn` |
| Kısıt | c = (u, a, op, v, s, w) | `schemas.Constraint` (`type`, `operator`, `value`, `strength`, `weight`) |
| Öznitelik kümesi | A | `ConstraintType` (date, time, budget, location, diet, capacity, accessibility, activity) |
| Operatörler | {=, ≠, ≤, ≥, ∈, ∉} | `Operator` |
| Plan | p = (mekan, tarih, saat, bütçe) | `schemas.EventPlan` |
| Ortam (mekan DB) | V | `env.event_planning.VenueDB` |
| Sağlama | p ⊨ c | `env.event_planning.satisfies` |
| Uygulanabilirlik | ∃p: ∀c ∈ C, p ⊨ c | `env.event_planning.find_feasible_plan` |
| Çakışma | conflict(cᵢ, cⱼ) ⇔ ¬∃p: p ⊨ cᵢ ∧ p ⊨ cⱼ | `schemas.Conflict`, `ConflictType` |
| Kısıt çıkarıcı | E: m → {c} | `extract.ConstraintExtractor` |
| Dedektör | D: (M, C) → çakışma kümesi | `detect.ConflictDetector` |
| Strateji | π: (oturum, çakışmalar) → eylem | `strategies.CoordinationStrategy`, `schemas.Action` |
| Eylem uzayı | {proceed, ask, compromise, vote, override} | `ActionType` |
| Görev başarısı | tüm sert kısıtlar sağlandı | `eval.metrics.task_success` |
| Kullanıcı memnuniyeti | sat(u, p) ∈ [0, 1] | `RunResult.user_satisfaction` |
