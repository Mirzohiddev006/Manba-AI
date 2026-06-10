output "alb_dns" { value = aws_lb.main.dns_name }
output "api_url" { value = "https://${var.api_domain}" }
output "ecr_api" { value = aws_ecr_repository.repos["manba-api"].repository_url }
output "ecr_bot" { value = aws_ecr_repository.repos["manba-bot"].repository_url }
output "db_endpoint" { value = aws_db_instance.main.address }
