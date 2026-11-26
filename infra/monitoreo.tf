resource "aws_cloudwatch_metric_alarm" "errores_lambda" {
  alarm_name          = "${local.nombre}-errores-api"
  alarm_description   = "La API de citas tuvo errores en los últimos 5 minutos"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.correo_alertas == "" ? [] : [aws_sns_topic.alertas[0].arn]

  dimensions = {
    FunctionName = aws_lambda_function.api.function_name
  }
}

resource "aws_sns_topic" "alertas" {
  count = var.correo_alertas == "" ? 0 : 1
  name  = "${local.nombre}-alertas"
}

resource "aws_sns_topic_subscription" "correo" {
  count     = var.correo_alertas == "" ? 0 : 1
  topic_arn = aws_sns_topic.alertas[0].arn
  protocol  = "email"
  endpoint  = var.correo_alertas
}
