variable "aws_region" { default = "us-east-1" }
variable "project" { default = "manba" }
variable "env" { default = "production" }
variable "api_domain" { default = "api.loyiha.uz" }
variable "route53_zone_id" { type = string }
variable "db_instance_class" { default = "db.t4g.micro" }
variable "redis_node_type" { default = "cache.t4g.micro" }
variable "monthly_budget_usd" { default = "50" }
variable "alert_email" { type = string }

# Sekretlar — faqat tfvars/env orqali, hech qachon git ga emas
variable "db_password" {
  type      = string
  sensitive = true
}
variable "bot_token" {
  type      = string
  sensitive = true
}
variable "anthropic_api_key" {
  type      = string
  sensitive = true
}
variable "jwt_secret" {
  type      = string
  sensitive = true
}
variable "admin_jwt_secret" {
  type      = string
  sensitive = true
}
variable "webhook_secret_path" {
  type      = string
  sensitive = true
}
variable "webhook_secret_token" {
  type      = string
  sensitive = true
}
variable "click_secret_key" {
  type      = string
  sensitive = true
  default   = ""
}
variable "payme_secret_key" {
  type      = string
  sensitive = true
  default   = ""
}
