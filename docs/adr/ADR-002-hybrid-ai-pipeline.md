# ADR-002: Gibrid AI quvuri — regex-birinchi, LLM-zaxira, shablon-formatlash

**Holat:** Qabul qilingan · 2026-06-09

## Kontekst
Bibliografik formatlashda tinish belgilari (`. – `, `//`, `– B. 45–52.`) mutlaq aniq bo'lishi shart — bitta xato dissertatsiyani OAKdan qaytarishi mumkin. LLM generatsiyasi nondeterministik va qimmat (1000 foyd. = $30–80/oy).

## Qaror
Uch qatlamli quvur:
1. **Regex+evristika parser** — maydon ajratish, har maydonga confidence 0–1; umumiy ≥ 0.85 → LLM chaqirilmaydi (kutilgan qamrov: tipik manbalarning ~70–80%).
2. **LLM (Claude, structured output)** — faqat past-confidence holatlarda, faqat maydon ajratish uchun. JSON schema bilan majburlanadi, javob Pydantic `SourceFields` ga validatsiya qilinadi.
3. **Jinja2 shablon motori** — yakuniy satrni HAR DOIM faqat shu yig'adi. Shablonlar DB da versiyalanadi, admin panelda sinov maydonchasi bilan tahrirlanadi.

## Muqobillar
- Hammasi-LLM: tezkor MVP, lekin tinish belgisi kafolati yo'q, xarajat ~5–10×, latency har so'rovda 2–6 s. Rad etildi.
- Faqat-regex: arzon/tez, lekin notipik/buzuq kiritishlarda qamrov ~60% dan oshmaydi. Yetarli emas.

## Oqibatlar
(+) determinizm — 97% aniqlik o'lchanadigan va barqaror; LLM xarajati ~4–5× kam; shablon o'zgarishi kod relizisiz. (−) collation, evristikalar va confidence kalibrlash murakkab — 500+ etalon korpus bilan har relizda regression o'lchanadi (CI darvozasi).

## Invariant (arxitektura sharti)
`formatted_text` faqat `citation_core.render(fields, template)` dan chiqadi. LLM chiqishida `formatted_text` maydoni yo'q — sxema darajasida taqiqlangan.
