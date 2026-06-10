# ManbaAI ni AWS ga bepul kredit bilan qo'yish (EC2 + docker-compose)

> Eng arzon yo'l: bitta kichik EC2 server (~$10–15/oy → $100–200 kredit 6 oyga yetadi).
> Bot **polling** rejimida — domen, HTTPS, ALB kerak emas. Faqat SSH porti ochiq.

## 0. Bilib qo'ying (2026 tartibi)

- Yangi AWS akkaunt: ro'yxatdan o'tishda **$100 kredit**, 5 ta mashqni bajarib **yana +$100** (har biri $20: EC2 ishga tushirish, RDS, Lambda, Bedrock, Budgets).
- Bepul reja akkaunti **6 oy** yoki kredit tugaguncha ishlaydi — kredit tugashidan oldin xohlasangiz pullik rejaga o'tasiz (ma'lumotlar saqlanadi).
- Kreditlar EC2 ga ham ishlaydi (eski «faqat t2.micro» qoidasi yo'q).

## 1. AWS akkaunt ochish (10 daqiqa)

1. aws.amazon.com/free → **Create a free account**.
2. Email + parol → akkaunt nomi → telefon tasdiqlash → bank karta (tekshiruv uchun; bepul rejada o'zi yechmaydi).
3. **Free plan** ni tanlang (Paid emas!).
4. Kirgach yuqoridagi qidiruvdan **Billing → Credits** da $100 turganini tekshiring.
5. **+$100 olish:** konsol bosh sahifasidagi «Explore AWS» mashqlarini bajaring (har biri 5–10 daqiqa, $20 dan).

## 2. EC2 server yaratish (10 daqiqa)

1. Qidiruvdan **EC2** → **Launch instance**.
2. Sozlamalar:
   - **Name:** `manba-server`
   - **OS:** Ubuntu Server 24.04 LTS (64-bit Arm yoki x86)
   - **Instance type:** `t4g.small` (2 GB RAM, Arm — arzonroq) yoki `t3.small`
   - **Key pair:** Create new → nom: `manba-key` → **.pem** yuklab olinadi — YO'QOTMANG
   - **Network settings:** faqat **SSH (22)** ochiq, Source: **My IP**
   - **Storage:** 16 GB gp3
3. **Launch instance** → instans ro'yxatida **Public IPv4 address** ni ko'chirib oling (masalan `3.92.xx.xx`).

## 3. Serverga ulanish

Windows PowerShell da (`.pem` fayl Downloads da deb faraz qilamiz):

```powershell
ssh -i C:\Users\ibroh\Downloads\manba-key.pem ubuntu@3.92.xx.xx
```

«yes» deb tasdiqlaysiz — Ubuntu terminaliga tushasiz.

## 4. Loyihani serverga olib chiqish

Eng qulay — GitHub orqali (tavsiya):

```bash
# Kompyuteringizda (bir marta): github.com da private repo oching, keyin loyiha papkasida:
git init && git add -A && git commit -m "ManbaAI v1"
git remote add origin https://github.com/SIZNING_LOGIN/manba-ai.git
git push -u origin main
```

Serverda:

```bash
git clone https://github.com/SIZNING_LOGIN/manba-ai.git
cd manba-ai
```

(GitHub siz bo'lsa: `scp -i manba-key.pem -r C:\Users\ibroh\Downloads\Manba_AI ubuntu@IP:~/manba-ai` — sekinroq.)

## 5. Sozlash va ishga tushirish

```bash
cp .env.example .env
nano .env        # BOT_TOKEN=... ga YANGI tokenni yozing (eski tokenni BotFather da /revoke qiling!)
                 # DB_PASSWORD ham o'ylab topib yozing
bash scripts/ec2_setup.sh
```

Skript o'zi: Docker o'rnatadi → swap qo'shadi → konteynerlarni quradi → ishga tushiradi.
5–8 daqiqadan keyin botga `/start` yozing — **endi 24/7 ishlaydi.**

## 6. Kundalik buyruqlar

```bash
sudo docker compose -f docker-compose.server.yml logs -f bot    # bot loglari
sudo docker compose -f docker-compose.server.yml restart        # qayta yurgizish
sudo docker compose -f docker-compose.server.yml ps             # holat
git pull && sudo docker compose -f docker-compose.server.yml up -d --build   # yangilash
```

## 7. Xarajat nazorati (majburiy!)

1. **Billing → Budgets → Create budget** → Monthly, $15 → email ogohlantirish.
   (Bu o'zi +$20 kredit mashqlaridan biri — bir o'q bilan ikki quyon.)
2. Haftada bir **Billing → Credits** da qoldiqni ko'rib turing.
3. 6 oy tugashiga yaqin: yo pullik rejaga o'ting (server o'sha-o'sha ~$12/oy), yo serverni boshqa joyga ko'chiring (docker-compose tufayli ko'chirish 15 daqiqa).

## Keyingi bosqichlar (kredit yetarli bo'lganda)

- AI ulash: `.env` ga `ANTHROPIC_API_KEY` qo'shib `docker compose restart` — tartibsiz manbalar ham yuqori aniqlikda.
- Web App/Admin: Vercel ga bepul (README → «Vercel ulash»). U holda API ga HTTPS kerak bo'ladi — Caddy reverse-proxy yoki to'liq Terraform stack (`infra/`).
- PDF tahlili: S3+SQS kerak — to'liq stack bosqichida.
