# ManbaAI — AWS infratuzilma (TZ 10.1)
terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.70" }
  }
  # backend "s3" { ... } # holatni S3 da saqlash — deploy yo'riqnomasiga qarang
}

provider "aws" {
  region = var.aws_region
}

# === Tarmoq: VPC, 2 public + 2 private subnet, NAT ===
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "manba-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # xarajat optimallashuvi (boshlanish)
}

# === ECR ===
resource "aws_ecr_repository" "repos" {
  for_each             = toset(["manba-api", "manba-bot"])
  name                 = each.key
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

# === S3: PDF (30 kun) va eksport (7 kun) ===
resource "aws_s3_bucket" "pdf" {
  bucket = "${var.project}-pdf-${var.env}"
}

resource "aws_s3_bucket_lifecycle_configuration" "pdf" {
  bucket = aws_s3_bucket.pdf.id
  rule {
    id     = "expire-30d"
    status = "Enabled"
    expiration { days = 30 }
  }
}

resource "aws_s3_bucket" "export" {
  bucket = "${var.project}-export-${var.env}"
}

resource "aws_s3_bucket_lifecycle_configuration" "export" {
  bucket = aws_s3_bucket.export.id
  rule {
    id     = "expire-7d"
    status = "Enabled"
    expiration { days = 7 }
  }
}

# === SQS + DLQ ===
resource "aws_sqs_queue" "pdf_dlq" {
  name = "${var.project}-pdf-tasks-dlq"
}

resource "aws_sqs_queue" "pdf" {
  name                       = "${var.project}-pdf-tasks"
  visibility_timeout_seconds = 180
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.pdf_dlq.arn
    maxReceiveCount     = 3
  })
}

# === RDS PostgreSQL 16 ===
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "db" {
  name   = "${var.project}-db-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_db_instance" "main" {
  identifier              = "${var.project}-db"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  db_name                 = "manba"
  username                = "manba"
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  backup_retention_period = 7
  multi_az                = false # o'sishda yoqiladi
  skip_final_snapshot     = var.env != "production"
}

# === ElastiCache Redis ===
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project}-redis"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis" {
  name   = "${var.project}-redis-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id         = "${var.project}-redis"
  engine             = "redis"
  engine_version     = "7.1"
  node_type          = var.redis_node_type
  num_cache_nodes    = 1
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
}

# === Secrets Manager ===
resource "aws_secretsmanager_secret" "app" {
  name = "${var.project}/${var.env}/app"
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    BOT_TOKEN             = var.bot_token
    DATABASE_URL          = "postgresql+asyncpg://manba:${var.db_password}@${aws_db_instance.main.address}:5432/manba"
    REDIS_URL             = "redis://${aws_elasticache_cluster.main.cache_nodes[0].address}:6379/0"
    ANTHROPIC_API_KEY     = var.anthropic_api_key
    JWT_SECRET            = var.jwt_secret
    ADMIN_JWT_SECRET      = var.admin_jwt_secret
    WEBHOOK_SECRET_PATH   = var.webhook_secret_path
    WEBHOOK_SECRET_TOKEN  = var.webhook_secret_token
    CLICK_SECRET_KEY      = var.click_secret_key
    PAYME_SECRET_KEY      = var.payme_secret_key
  })
}
