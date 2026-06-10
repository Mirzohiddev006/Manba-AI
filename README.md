# ManbaAI — bibliografik assistent

Ilmiy manbalarni **OAK / O'zDSt** talablariga moslab avtomatik rasmiylashtiruvchi tizim:
Telegram bot + Telegram Web App (Mini App) + Admin panel + FastAPI backend — bitta monorepo.

> Texnik topshiriq: `ManbaAI_Texnik_Topshiriq_v2.docx` (v2.0). Dizayn: `docs/SYSTEM_DESIGN.md`, ADRlar: `docs/adr/`.

## Arxitektura qisqacha

- **Gibrid AI quvuri** (ADR-002): regex+evristika parser → confidence ≥ 0.85 bo'lsa LLM chaqirilmaydi → past bo'lsa Claude API (structured output, faqat maydon ajratish) → **yakuniy satrni faqat Jinja2 shablon motori yig'adi** (LLM hech qachon satr yozmaydi — arxitektura invarianti).
- **citation-core** — sof Python paket: 9 manba turi, OAK 3-guruh saralash (kirill-lotin aralash collation), imlo (hunspell+lug'at), DOCX eksport (TNR 14, 1.5, osma xat), kirill↔lotin translit, BibTeX/RIS.
- AWS (ECS Fargate) + Vercel (webapp/admin). Serverless varianti: `apps/api/app/lambda_handler.py` (Mangum).

## Tuzilma

```
apps/bot       — aiogram 3, webhook (lokal: polling), i18n (uz/uz-kirill/ru), FSM Redis da
apps/api       — FastAPI, SQLAlchemy 2 async, Alembic, PDF worker (SQS+Tesseract OCR)
apps/webapp    — React 18 + Vite, FSD, Telegram Mini App, MSW mock → Vercel
apps/admin     — React 18 + Vite, shadcn-uslub, RBAC, TOTP → Vercel
packages/citation-core — bibliografik yadro + 60+ etalon test (aniqlik darvozasi ≥ 97%)
packages/shared-types  — OpenAPI dan TS turlari (pnpm generate)
infra/         — Terraform (VPC, ECS, RDS, Redis, S3, SQS, ALB, ACM, Route53, Secrets, alarmlar)
scripts/       — smoke_test.py, create_admin.py
```

## Lokal ishga tushirish

```bash
cp .env.example .env            # BOT_TOKEN va boshqalarni to'ldiring
docker-compose up --build       # postgres, redis, localstack, api, worker, bot (polling)

# Localstack da S3/SQS yaratish (bir marta):
aws --endpoint-url=http://localhost:4566 s3 mb s3://manba-pdf
aws --endpoint-url=http://localhost:4566 s3 mb s3://manba-export
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name manba-pdf-tasks

# Smoke-test (parse → list → export):
python scripts/smoke_test.py

# Birinchi superadmin:
python scripts/create_admin.py admin@manba.uz 'KuchliParol!'
```

Frontendlar:

```bash
pnpm install
pnpm --filter @manba/webapp dev    # :5173 (MSW mock yoqilgan — backend shart emas)
pnpm --filter @manba/admin dev     # :5174
```

Testlar:

```bash
uv sync --all-packages
uv run pytest packages/citation-core/tests -s        # aniqlik hisoboti chiqadi
uv run pytest apps/api/tests apps/bot/tests
pnpm turbo typecheck build
```

## AWS ga deploy (TZ 10.2 — 10 qadam)

1. **AWS akkaunt**: IAM foydalanuvchi (admin emas — ECS/ECR/RDS/S3/SQS/EC2-network policy), MFA, billing alert $50 (Terraform `aws_budgets_budget` ham yaratadi).
2. **Terraform**: `cd infra && cp terraform.tfvars.example terraform.tfvars` (sekretlarni to'ldiring) → `terraform init && terraform apply`. VPC, subnetlar, NAT shu yerda yaratiladi.
3. RDS + ElastiCache private subnetlarda ko'tariladi; ulanishlar **Secrets Manager** ga yoziladi (`manba/production/app`).
4. ECR ga birinchi push: `aws ecr get-login-password | docker login …` → `docker build -f apps/api/Dockerfile -t $ECR/manba-api:latest .` → push (bot ham). Keyin CI avtomatlashtiradi.
5. ECS klaster/servislar Terraform dan keladi; env lar Secrets Manager dan olinadi.
6. ALB 443 (ACM sertifikat DNS validatsiya) → Route 53 `api.loyiha.uz` A-yozuvi — Terraform da.
7. **Telegram webhook**: bot servisi ishga tushganda o'zi `setWebhook` qiladi (`https://api.loyiha.uz/webhook/{WEBHOOK_SECRET_PATH}`, `secret_token` bilan). Qo'lda: `curl "https://api.telegram.org/bot$TOKEN/setWebhook?url=...&secret_token=..."`.
8. **Migratsiyalar**: one-off ECS task — `aws ecs run-task … --overrides '{"containerOverrides":[{"name":"api","command":["alembic","upgrade","head"]}]}'`.
9. CloudWatch alarmlar (5xx>1%, SQS>100) Terraform da; Sentry: `SENTRY_DSN` env.
10. **Smoke-test**: `python scripts/smoke_test.py https://api.loyiha.uz` + botda /start → manba → eksport.

## Vercel ulash (monorepo)

Ikkita Vercel loyihasi, bitta repo:

| Loyiha | Root Directory | Env |
|---|---|---|
| manba-webapp | `apps/webapp` | `VITE_API_BASE=https://api.loyiha.uz`, `VITE_USE_MOCKS=0` |
| manba-admin | `apps/admin` (domen: admin.loyiha.uz) | `VITE_API_BASE=https://api.loyiha.uz` |

Ignored Build Step (faqat tegishli papka o'zgarganda deploy):
`git diff HEAD^ HEAD --quiet -- apps/webapp packages/shared-types`

## BotFather sozlamalari

1. `/newbot` → token → Secrets Manager / `.env`.
2. `/setmenubutton` → **Menu Button → Web App URL**: `https://webapp.loyiha.uz` (Vercel domeni).
3. `/setcommands`:
```
new - Yangi manba kiritish
list - Mening ro'yxatlarim
export - Word (.docx) yuklab olish
spell - Imlo tekshiruvi
settings - Sozlamalar
premium - Tarif rejalari
feedback - Fikr bildirish
help - Qo'llanma
```

## Sifat darvozalari (CI)

- citation-core etalon to'plamda aniqlik **≥ 97%** — pasaysa PR bloklanadi (`--accuracy-threshold=0.97`);
- ruff + mypy + pytest (api, bot) + eslint + tsc + vitest;
- main ga merge → docker build → ECR → ECS rolling update (health-check bilan).

## Admin qo'llanmasi (qisqa)

- Kirish: email + parol + TOTP (birinchi admin: `scripts/create_admin.py`).
- **Format shablonlari**: Jinja2 sintaksisida yangi versiya yozing → «▶ Sinab ko'rish» (namunaviy manba bilan) → «Saqlash». Faol shablon keyingi parse dan kuchga kiradi, kod relizi shart emas.
- **Lug'at**: foydalanuvchi taklif qilgan so'zlar `pending` holatda — ✅/❌ moderatsiya.
- **AI monitoring**: past-confidence tahlillar — etalon korpusga qo'shish uchun nomzodlar.
- Rollar: superadmin (hammasi) / moderator (foydalanuvchi, feedback, broadcast) / kontent-menejer (shablon, lug'at).
