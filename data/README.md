# Veri

Şemaların kesin tanımı: [`src/mucon/schemas.py`](../src/mucon/schemas.py). Bu dosya özettir;
çelişki olursa kod geçerlidir. Tüm dosyalar UTF-8 JSON'dur.

| Klasör | İçerik | Git |
|---|---|---|
| `raw/` | Dış kaynaklardan ham veri (benchmark çıktıları vb.) | hayır |
| `scenarios/` | Üretilmiş senaryolar, `<scenario_id>.json` (`Scenario`) | evet |
| `labels/` | İnsan etiketleri, `<annotator>.jsonl` (satır başına `ConflictLabel`) | evet |
| `processed/` | Türetilmiş veri: `venues.json`, eğitim/test bölmeleri | evet |

## Scenario
| Alan | Tip | Açıklama |
|---|---|---|
| `id` | str | `sc-0001` |
| `domain` | `"event_planning"` | |
| `description` | str | Senaryonun kısa açıklaması |
| `personas` | list[UserPersona] (≥2) | `user` (`id`, `name`, `rank`), `persona`, `hidden_preferences: list[Constraint]` |
| `scripted_messages` | list[Message] | Dedektör değerlendirmesi için sabit diyalog (opsiyonel) |
| `gold_labels` | list[ConflictLabel] | Senaryoya gömülü etiketler (opsiyonel) |
| `seed` | int \| null | Üretim seed'i |

## Session
Agent'ın gördüğü canlı oturum; gizli tercihler **yoktur**.
`id`, `scenario_id`, `users: list[User]`, `messages: list[Message]`, `constraints: list[Constraint]`.

## Message
| Alan | Tip | Açıklama |
|---|---|---|
| `id` | str | `m1` |
| `role` | `user` \| `agent` \| `system` | |
| `user_id` | str \| null | `role=user` ise zorunlu |
| `turn` | int ≥ 0 | Oturumdaki sıra |
| `text` | str | |
| `timestamp` | datetime \| null | |

## Constraint
| Alan | Tip | Açıklama |
|---|---|---|
| `id`, `user_id` | str | |
| `type` | `date`, `time`, `budget`, `location`, `diet`, `capacity`, `accessibility`, `activity`, `other` | |
| `operator` | `eq`, `neq`, `lte`, `gte`, `in`, `not_in` | |
| `value` | str \| int \| float \| bool \| list[str] | Tarih/saat ISO string |
| `strength` | `hard` \| `soft` | Görev başarısı yalnızca `hard` kısıtlara bakar |
| `weight` | float ≥ 0 | Memnuniyet hesabında ağırlık |
| `source_message_id`, `raw_text` | str \| null | İzlenebilirlik |

## ConflictLabel
| Alan | Tip | Açıklama |
|---|---|---|
| `scenario_id` | str | |
| `message_ids` | list[str] (≥2) | Çakışan (veya çakışmayan) mesaj çifti |
| `has_conflict` | bool | |
| `conflict_type` | `direct`, `range`, `indirect`, `revision` \| null | `has_conflict=true` ise zorunlu, değilse boş |
| `annotator` | str | `eren`, `yusuf`, ... |
| `notes` | str | |

> Çakışma türleri taslaktır; H2'de etiketleme kılavuzu ile kesinleşecek.
