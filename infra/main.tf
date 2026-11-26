locals {
  usa_emulador = var.endpoint != ""
  nombre       = "patitas-${var.ambiente}"
  arquitectura = local.usa_emulador ? "x86_64" : "arm64"
  raiz         = "${path.module}/.."
}

resource "aws_dynamodb_table" "citas" {
  name                        = "${local.nombre}-citas"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "pk"
  deletion_protection_enabled = !local.usa_emulador && var.ambiente == "prod"

  attribute {
    name = "pk"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

data "aws_iam_policy_document" "asumir_lambda" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.nombre}-lambda"
  assume_role_policy = data.aws_iam_policy_document.asumir_lambda.json
}

data "aws_iam_policy_document" "permisos_lambda" {
  statement {
    sid = "TablaCitas"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:Scan",
    ]
    resources = [aws_dynamodb_table.citas.arn]
  }

  statement {
    sid       = "Trazas"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
    resources = ["*"]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.nombre}-lambda"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.permisos_lambda.json
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.nombre}-api"
  retention_in_days = var.retencion_logs_dias
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${local.raiz}/backend"
  output_path = "${path.module}/build/lambda.zip"
  excludes    = ["__pycache__"]
}

resource "aws_lambda_function" "api" {
  function_name                  = "${local.nombre}-api"
  role                           = aws_iam_role.lambda.arn
  runtime                        = "python3.12"
  handler                        = "handler.lambda_handler"
  architectures                  = [local.arquitectura]
  filename                       = data.archive_file.lambda.output_path
  source_code_hash               = data.archive_file.lambda.output_base64sha256
  memory_size                    = 128
  timeout                        = 10
  reserved_concurrent_executions = var.concurrencia_maxima

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.citas.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda, aws_iam_role_policy.lambda]
}
