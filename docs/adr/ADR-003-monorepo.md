# ADR-003: Bitta monorepo — uv (Python) + pnpm/turbo (TS)

**Holat:** Qabul qilingan · 2026-06-09

## Kontekst
4 ta ilova (bot, api, webapp, admin) + 2 ta paket (citation-core, shared-types), bitta buyurtmachi, kichik jamoa. Frontend Vercel ga, backend AWS ga deploy bo'ladi.

## Qaror
Bitta GitHub repo. Python tomonda `uv` workspace (apps/bot, apps/api, packages/citation-core — bitta lockfile, citation-core editable-install). TS tomonda `pnpm` workspace + `turbo` (webapp, admin, shared-types). Vercel: 2 loyiha, Root Directory `apps/webapp` / `apps/admin`, Ignored Build Step bilan faqat tegishli o'zgarishda deploy.

## Asoslar
- citation-core bot ham api ham ishlatadi — versiya drift xavfi poly-repo da yuqori.
- shared-types OpenAPI dan generatsiya qilinadi — bitta repoda kontrakt sinxronligi PR darajasida tekshiriladi.
- CI bitta joyda: citation-core aniqlik regressi har qanday PR ni bloklaydi.

## Oqibatlar
(+) atomar o'zgarishlar, bitta CI, oson onboarding. (−) CI vaqtini boshqarish uchun path-filter kerak (ci.yml da `paths` shartlari); repo o'sganda turbo remote cache qo'shiladi.
