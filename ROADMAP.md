# Yol Haritası (GP1)

| Hafta | Tarih | Eren | Yusuf | Hocaya giden |
|---|---|---|---|---|
| H1 | 2–8 Kas | Repo kurulumu, Muses-Bench'in çalıştırılması | MAP + 3–4 yeni makale | Haftalık rapor |
| H2 | 9–15 Kas | Problemin formal tanımı, Harness-MU kodunun incelenmesi | Senaryo şeması, çakışma türleri, etiketleme kılavuzu | 1. ara rapor (literatür + problem tanımı) |
| H3 | 16–22 Kas | Senaryo üreteci, kısıt çıkarıcı v0 | İlk 50 senaryonun etiketlenmesi | Haftalık rapor |
| H4 | 23–29 Kas | Simülasyon altyapısı, S0 | ~300 senaryo + etiketler, S1/S2 | Haftalık rapor |
| H5 | 30 Kas–6 Ara | Kural + zero-shot dedektör, P/R/F1 | Veri seti istatistikleri, hata analizi | 2. ara rapor |
| H6 | 7–13 Ara | DeBERTa fine-tune | S3 uzlaştırma | Haftalık rapor |
| H7 | 14–20 Ara | Uçtan uca pipeline, pilot | S4 oylama/Borda | Haftalık rapor |
| H8 | 21–27 Ara | Tam deneyler | Metrikler, Wilcoxon, grafikler | Haftalık rapor |
| H9 | 28 Ara–3 Oca | Rapor: yöntem ve bulgular | Rapor: giriş ve literatür | 3. ara rapor |
| H10 | 4–8 Oca | Son düzeltmeler, sunum | Biçimlendirme, sunum | GP1 teslimi |

**Kritik nokta:** H4 sonunda veri seti ve baseline'lar hazır olmalı.

Koddaki `# TODO(Hn)` işaretleri bu tablodaki haftalara karşılık gelir:
`grep -rn "TODO(H3)" src/`
