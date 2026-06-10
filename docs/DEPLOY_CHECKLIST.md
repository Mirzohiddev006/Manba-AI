# Deploy Checklist: ManbaAI V1 (AWS ECS + Vercel)

**Sana:** ___ | **Deploy qiluvchi:** ___

## Pre-Deploy

- [ ] CI yashil: ruff + mypy + pytest (citation-core aniqlik ≥ 97%) + eslint + tsc + vitest
- [ ] Code review tasdiqlangan (`docs/CODE_REVIEW.md` dagi 🔴 lar yopiq)
- [ ] `terraform plan` ko'rib chiqildi — kutilmagan destroy yo'q
- [ ] `terraform.tfvars` sekretlari to'ldirilgan, git ga TUSHMAGAN (`.gitignore` da `*.tfvars`)
- [ ] Alembic migratsiya staging DB nusxasida sinab ko'rildi (`alembic upgrade head` + `downgrade -1`)
- [ ] Secrets Manager dagi barcha 10 kalit to'ldirilgan (BOT_TOKEN, DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, JWT_SECRET, ADMIN_JWT_SECRET, WEBHOOK_SECRET_PATH/TOKEN, CLICK/PAYME)
- [ ] Rollback rejasi: oldingi ECS task definition revision raqami yozib olindi
- [ ] Billing alert ($50) va byudjet alarmi faol

## Deploy

- [ ] Docker obrazlar ECR ga push qilindi (api + bot), teg = git SHA
- [ ] Migratsiya one-off ECS task bilan bajarildi (8-qadam, README)
- [ ] ECS rolling update tugadi, target group health-check `healthy`
- [ ] Telegram webhook o'rnatildi: `getWebhookInfo` → to'g'ri URL + `last_error_message` bo'sh
- [ ] Vercel: webapp + admin production deploy, `VITE_API_BASE` to'g'ri, `VITE_USE_MOCKS=0`
- [ ] BotFather Menu Button → Web App URL yangilandi
- [ ] Smoke-test: `python scripts/smoke_test.py https://api.loyiha.uz` ✅
- [ ] Qo'lda oqim: /start → manba yuborish → kartochka → ➕ → /export → .docx ochildi
- [ ] 15 daqiqa monitoring: CloudWatch 5xx, SQS chuqurligi, LLM xarajati

## Post-Deploy

- [ ] Admin panelga TOTP bilan kirish ishlaydi (admin.loyiha.uz)
- [ ] Sentry da yangi release xatosiz
- [ ] CHANGELOG yangilandi, buyurtmachiga xabar berildi
- [ ] lex.uz selektor smoke-testi rejalashtirilgan (kunlik)

## Rollback triggerlari

- 5xx > 1% (5 daqiqa davomida) → ECS service oldingi task definition ga qaytariladi
- Webhook `last_error_message` to'lib boradi → bot servisini oldingi revisionga qaytarish
- citation-core formatlash regressi (foydalanuvchi shikoyati) → admin panelda shablon versiyasini orqaga almashtirish (kod relizisiz)
- SQS chuqurligi > 100 va worker scale-out yordam bermayapti → PDF qabulini vaqtincha o'chirish (texnik tanaffus rejimi)
