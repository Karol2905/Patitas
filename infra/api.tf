resource "aws_api_gateway_rest_api" "api" {
  name = "${local.nombre}-api"
  tags = local.usa_emulador ? { "floci:override-id" = local.nombre } : {}

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_resource" "citas" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "citas"
}

resource "aws_api_gateway_resource" "cita" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.citas.id
  path_part   = "{id}"
}

locals {
  rutas = {
    citas = aws_api_gateway_resource.citas.id
    cita  = aws_api_gateway_resource.cita.id
  }
}

resource "aws_api_gateway_method" "ruta" {
  for_each      = local.rutas
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = each.value
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "ruta" {
  for_each                = local.rutas
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = each.value
  http_method             = aws_api_gateway_method.ruta[each.key].http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.api.invoke_arn
}

resource "aws_lambda_permission" "api" {
  statement_id  = "PermitirApiGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    version = sha1(jsonencode([
      aws_api_gateway_resource.citas.id,
      aws_api_gateway_resource.cita.id,
      aws_api_gateway_method.ruta,
      aws_api_gateway_integration.ruta,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  rest_api_id          = aws_api_gateway_rest_api.api.id
  deployment_id        = aws_api_gateway_deployment.api.id
  stage_name           = var.ambiente
  xray_tracing_enabled = true
}

locals {
  url_api = (
    local.usa_emulador
    ? "${var.endpoint}/restapis/${aws_api_gateway_rest_api.api.id}/${aws_api_gateway_stage.api.stage_name}/_user_request_"
    : aws_api_gateway_stage.api.invoke_url
  )
}
