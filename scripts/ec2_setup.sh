#!/usr/bin/env bash
# ManbaAI — yangi Ubuntu EC2 serverni tayyorlash (bir marta ishga tushiriladi)
set -euo pipefail

echo "=== 1/4 Docker o'rnatilmoqda ==="
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER

echo "=== 2/4 Swap (1GB RAM li serverlar uchun) ==="
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "=== 3/4 .env tekshiruvi ==="
if [ ! -f .env ]; then
  echo "DIQQAT: .env fayl yo'q! .env.example dan nusxalab BOT_TOKEN ni yozing:"
  echo "  cp .env.example .env && nano .env"
  exit 1
fi
grep -q "BOT_TOKEN=.*:" .env || { echo "DIQQAT: .env da BOT_TOKEN to'ldirilmagan"; exit 1; }

echo "=== 4/4 Ishga tushirish ==="
sudo docker compose -f docker-compose.server.yml up -d --build
sleep 10
sudo docker compose -f docker-compose.server.yml ps
echo ""
echo "✅ Tayyor! Loglarni ko'rish: sudo docker compose -f docker-compose.server.yml logs -f bot"
