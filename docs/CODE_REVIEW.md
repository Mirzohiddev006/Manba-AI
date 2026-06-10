# Code Review: ManbaAI monorepo (o'z-o'zini tekshiruv, V1)

## Xulosa
Arxitektura invariantlari (LLM hech qachon yakuniy satr yozmaydi; formatlash faqat Jinja2) kod darajasida majburlangan. Auth konturlari (initData HMAC, TOTP, RBAC) testlar bilan qoplangan. Quyidagi topilmalardan 🔴/🟠 darajadagilari shu reviewda **tuzatildi**.

## Tuzatilgan muammolar

| # | Fayl | Muammo | Daraja | Holat |
|---|------|--------|--------|-------|
| 1 | `apps/api/app/routers/admin.py` | Admin login da IP rate limit yo'q edi (TZ 11 talabi) — brute-force xavfi | 🔴 | ✅ 10 urinish/15 daq (Redis) |
| 2 | `apps/api/app/routers/sources.py` | PATCH dagi yaroqsiz maydon qiymati 500 qaytarardi | 🟠 | ✅ 422 + tushunarli xabar |
| 3 | `citation-core` confidence formulasi | Tipik kitob 0.785 < 0.85 — har kitobda LLM behuda chaqilardi (xarajat!) | 🟠 | ✅ field_score×(0.5+0.5×type_conf) |
| 4 | `apps/api` bcrypt | passlib + bcrypt 4.x nomuvofiqligi loginni butunlay buzardi | 🔴 | ✅ `bcrypt<4` pin |

## Qabul qilingan risklar / kuzatuvlar

| # | Joy | Kuzatuv | Izoh |
|---|-----|---------|------|
| 1 | `payments/click` | MD5 imzo (`noqa: S324`) | Click protokoli talabi — tanlov yo'q; idempotentlik `external_id` unique bilan |
| 2 | `bot/api_client.py` | Token keshi xotirada cheksiz o'sadi | Past xavf (token 30 daq TTL, dict yengil); V1.1 da LRU/TTL kesh |
| 3 | `config.py` dev defaultlari | `dev-jwt-secret` kabi qiymatlar | Faqat dev; prodda Secrets Manager majburiy (Terraform secrets blokisiz task ko'tarilmaydi) |
| 4 | CORS dev rejimda `*` | `env=dev` da | Prod ro'yxati: webapp + admin domenlari |
| 5 | `lists/_resort` | Har qo'shishda O(n log n) qayta saralash | n ≤ 500 (dissertatsiya ro'yxati) — yetarli; katta ro'yxatda incremental insert |
| 6 | `lexuz_service` | Global rate-limit bitta protsess ichida | Ko'p worker da Redis-based limiter kerak (V2 da scraper alohida worker — TZ 16.2 ga mos) |

## Xavfsizlik tekshiruvi (OWASP)

- **Injection**: faqat SQLAlchemy parametrlangan so'rovlar; raw SQL yo'q ✅
- **Auth**: initData HMAC-SHA256 + auth_date ≤ 1h (testlar: tampered/eskirgan rad) ✅; admin bcrypt+TOTP majburiy ✅; JWT kind ajratilgan (user/admin/refresh) ✅
- **Sekretlar**: kodda birorta token yo'q (`pydantic-settings`, `.env.example`, Secrets Manager); tfvars `sensitive=true` ✅
- **SSRF**: tashqi so'rovlar faqat belgilangan hostlarga (CrossRef/OpenLibrary/lex.uz); foydalanuvchi URL fetch qilinmaydi ✅
- **Fayl yuklash**: PDF magic-byte (`%PDF`) + hajm tekshiruvi; S3 lifecycle 30 kun ✅ (ClamAV skan — V1.1 backlog)
- **To'lovlar**: imzo tekshiruvi + `external_id` unique (idempotentlik) ✅

## Performans

- JSONB `GIN` indeks (sources.fields); FK indekslar ✅
- N+1 yo'q: `selectinload` ro'yxat detallarida ✅
- LLM xarajati: qoidaviy qamrov etalonda 100% — LLM faqat notipik kiritishlarda ✅
- DOCX 200 manba ≪ 5 s (python-docx, sinxron yo'lda kichik ish) ✅

## Verdikt
**Approve** — V1 mezonlariga tayyor; «Qabul qilingan risklar» bo'limi V1.1 backlogi sifatida kuzatilsin.
