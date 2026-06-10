# ADR-001: Hisoblash platformasi — ECS Fargate (Lambda zaxira yo'li bilan)

**Holat:** Qabul qilingan · 2026-06-09

## Kontekst
Backend (api, bot, pdf-worker) AWS da ishlashi kerak. TZ 10.1 Fargate ni asosiy, 10.3 serverless ni arzon-start varianti deb belgilaydi. LLM so'rovlari 6 s gacha, PDF tahlil 90 s gacha — API Gateway 29 s timeout bilan ziddiyatli.

## Qaror
ECS Fargate — asosiy production target. Kod Lambda-ga ko'chirishga tayyor qilinadi: FastAPI ilovasi `Mangum` adapteri bilan o'raladi (`apps/api/lambda_handler.py`), worker SQS-trigger Lambda sifatida ham ishlaydigan sof funksiya qilib yoziladi.

## Asoslar
- PDF worker 90 s ishlaydi — Lambda 15 daq limitiga sig'adi, lekin API Gateway 29 s sinxron limitiga LLM parse ba'zan yaqinlashadi; Fargate da bu muammo yo'q.
- Webhook bot uchun sovuq start (1–2 s) Telegram 60 s timeoutiga sig'adi, lekin UX talabiga (javob ≤1 s) zid.
- Fargate: $35–60/oy vs Lambda $3–8/oy — start bosqichida farq sezilarli, shuning uchun Mangum yo'li saqlanadi.

## Oqibatlar
(+) timeout cheklovlari yo'q, doimiy issiq konteyner, oddiy lokal-prod paritet (bir xil Docker obraz). (−) minimal $50+/oy xarajat; trafik juda past bo'lsa serverless variantga `infra/serverless/` qo'shish mumkin (kod o'zgarmaydi).
