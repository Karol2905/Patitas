terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.6"
    }
  }
}

provider "aws" {
  region                      = var.region
  access_key                  = local.usa_emulador ? "test" : null
  secret_key                  = local.usa_emulador ? "test" : null
  skip_credentials_validation = local.usa_emulador
  skip_metadata_api_check     = local.usa_emulador
  skip_requesting_account_id  = local.usa_emulador
  s3_use_path_style           = local.usa_emulador

  dynamic "endpoints" {
    for_each = local.usa_emulador ? [var.endpoint] : []
    content {
      apigateway = endpoints.value
      cloudwatch = endpoints.value
      dynamodb   = endpoints.value
      iam        = endpoints.value
      lambda     = endpoints.value
      logs       = endpoints.value
      s3         = endpoints.value
      sns        = endpoints.value
      sts        = endpoints.value
    }
  }

  default_tags {
    tags = {
      proyecto = "patitas"
      ambiente = var.ambiente
    }
  }
}
