# ManbaAI — Tizim dizayni (v1.0)

> Manba: `ManbaAI_Texnik_Topshiriq_v2.docx` (TZ v2.0, 09.06.2026). Ushbu hujjat TZ ni kod darajasidagi qarorlarga aylantiradi.

## 1. Talablar xulosasi

**Funksional:** erkin matn / PDF / URL / DOI / ISBN → strukturalangan manba → O'zDSt/OAK formatidagi bibliografik satr → ro'yxat boshqaruvi → DOCX eksport (OAK 3-ilova). Qo'shimcha: imlo tekshiruvi (uz-hunspell), kirill↔lotin, lex.uz qidiruv, DOI/ISBN lookup, BibTeX/RIS, jamoaviy ish, OAK jurnallar belgisi, OCR.

**Nofunksional:** qoidaviy tahlil ≤1 s; LLM bilan ≤6 s; PDF 150 manba ≤90 s; DOCX 200 manba ≤5 s; formatlash aniqligi ≥97%; imlo precision ≥95%; uptime ≥99.5%; 1000 parallel foydalanuvchi.

**Cheklovlar:** bitta monorepo; AWS (backend) + Vercel (frontend); LLM xarajati gibrid quvur bilan minimallashtiriladi.

## 2. Servis chegaralari

| Servis | Texnologiya | Mas'uliyat | Nima EMAS |
|---|---|---|---|
| `apps/bot` | Python 3.12, aiogram 3, webhook | Telegram UI, FSM, i18n, kartochkalar | Biznes-mantiq yo'q — hammasi API orqali |
| `apps/api` | FastAPI, SQLAlchemy 2 async | REST, auth, DB, navbatlar, to'lovlar, admin | Formatlash mantiqi yo'q — citation-core ga delegatsiya |
| `apps/api/workers` | Python, SQS consumer | PDF/OCR tahlili, lex.uz scraper, broadcast | HTTP qabul qilmaydi |
| `packages/citation-core` | Sof Python paket | Parsing, confidence, shablon formatlash, saralash, imlo, eksport, translit | DB/HTTP/Telegram ga bog'lanmaydi (faqat LLM client interfeysi DI orqali) |
| `apps/webapp` | React 18, Mini App | Murakkab tahrirlash UI | To'g'ridan DB yo'q |
| `apps/admin` | React 18, shadcn/ui | Boshqaruv, monitoring | — |
| `packages/shared-types` | TS (OpenAPI dan gen.) | API kontraktlari | — |

**Asosiy invariant:** yakuniy bibliografik satrni faqat Jinja2 shablon motori yig'adi. LLM faqat maydon ajratadi (structured output). Bu kod darajasida majburlanadi: LLM javobi `SourceFields` Pydantic modeliga parse qilinadi, `formatted_text` ni faqat `citation_core.render()` ishlab chiqaradi.

## 3. Ma'lumotlar oqimi (parse)

```
matn → preprocess (yozuv aniqlash, tozalash, satr ajratish)
     → rule parser (tur aniqlash + maydonlar + per-field confidence)
     → umumiy confidence ≥ 0.85 ? ──ha──► validate → Jinja2 render
                                  └─yo'q─► LLM extract (JSON schema) → merge → validate → Jinja2 render
```

PDF: `POST /pdf/upload` → S3 presigned → SQS → worker (matn qatlami? yo'q→Tesseract OCR) → adabiyotlar bo'limi topiladi → har satr yuqoridagi quvurga → natija DB ga, bot push.

## 4. Ma'lumotlar modeli

TZ 7-bo'lim + 16.10 jadvallar aynan qabul qilinadi (users, reference_lists, sources, list_items, templates, dictionary_words, subscriptions, payments, admin_users, audit_logs, llm_usage, broadcasts, feedback, lex_documents, oak_journals, list_shares, item_comments, ocr_tasks, pdf_tasks). `sources.fields` — JSONB (GIN), `source_type` — Postgres enum (9 tur). Redis: FSM, kunlik limit (`limit:{tg_id}:{date}`, TTL 24h), DOI/ISBN kesh (30 kun), SQS metrikalar.

## 5. API kontrakti

TZ 8-bo'lim + 16.10 to'liq. Auth ikki kontur:
- **User:** `POST /auth/telegram` — initData HMAC-SHA256 (secret = HMAC("WebAppData", bot_token)), `auth_date ≤ 3600 s` → JWT (30 daq).
- **Admin:** email+bcrypt+TOTP → access 15 daq + refresh 7 kun, RBAC depends (superadmin/moderator/kontent-menejer).

## 6. Kesh va navbat strategiyasi

| Nima | Qayer | TTL |
|---|---|---|
| DOI/ISBN javoblari | Redis | 30 kun |
| lex.uz hujjatlari | Postgres `lex_documents` | 90 kun |
| Kunlik limitlar | Redis counter | kun oxiri |
| FSM holatlari | Redis (aiogram RedisStorage) | 7 kun |
| PDF tahlil | SQS + DLQ (3 retry) | — |

## 7. Masshtab va ishonchlilik

Yuk bahosi: 1000 faol foyd. × 10 manba/kun ≈ 0.12 RPS o'rtacha, pik ~50 RPS → api 2–10 Fargate task autoscaling (CPU 70%); pdf-worker 0–5 (SQS chuqurligi > 10). RDS t4g.micro dan boshlanadi, Multi-AZ keyin. Alarmlar: 5xx > 1%, SQS > 100, LLM kunlik byudjet.

## 8. Trade-offlar (qaror → ADR)

1. ECS Fargate (asosiy) vs Lambda (arzon start) → ADR-001
2. Gibrid quvur (regex-birinchi, LLM-zaxira) vs hammasi-LLM → ADR-002
3. Bitta monorepo (uv + pnpm + turbo) vs poly-repo → ADR-003

## 9. O'sishda qayta ko'riladiganlar

GROBID ni alohida konteyner sifatida qo'shish (hozir qoidaviy bo'lim-topish yetarli); Aurora ga ko'chish 10k+ foydalanuvchida; LLM korpus feedback-loop (admin paneldagi past-confidence ro'yxatidan avtomatik fixture generatsiya).
