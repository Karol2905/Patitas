output "url_api" {
  description = "URL base de la API de citas"
  value       = local.url_api
}

output "url_sitio" {
  description = "URL del sitio web"
  value       = local.url_sitio
}

output "tabla" {
  description = "Nombre de la tabla de DynamoDB"
  value       = aws_dynamodb_table.citas.name
}

output "funcion" {
  description = "Nombre de la función Lambda"
  value       = aws_lambda_function.api.function_name
}
