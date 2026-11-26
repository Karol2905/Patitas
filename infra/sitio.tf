resource "aws_s3_bucket" "sitio" {
  bucket        = "${local.nombre}-sitio"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "sitio" {
  bucket = aws_s3_bucket.sitio.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "sitio" {
  bucket                  = aws_s3_bucket.sitio.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "sitio_publico" {
  statement {
    sid       = "LecturaPublica"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.sitio.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "sitio" {
  bucket     = aws_s3_bucket.sitio.id
  policy     = data.aws_iam_policy_document.sitio_publico.json
  depends_on = [aws_s3_bucket_public_access_block.sitio]
}

resource "aws_s3_bucket_website_configuration" "sitio" {
  count  = local.usa_emulador ? 0 : 1
  bucket = aws_s3_bucket.sitio.id

  index_document {
    suffix = "index.html"
  }
}

locals {
  carpeta_sitio = "${local.raiz}/frontend"
  archivos_sitio = [
    for archivo in fileset(local.carpeta_sitio, "**") : archivo
    if archivo != "config.js"
  ]
  tipos_contenido = {
    html = "text/html; charset=utf-8"
    css  = "text/css; charset=utf-8"
    js   = "application/javascript; charset=utf-8"
    webp = "image/webp"
    jpg  = "image/jpeg"
    png  = "image/png"
    svg  = "image/svg+xml"
  }
}

resource "aws_s3_object" "sitio" {
  for_each      = toset(local.archivos_sitio)
  bucket        = aws_s3_bucket.sitio.id
  key           = each.value
  source        = "${local.carpeta_sitio}/${each.value}"
  etag          = filemd5("${local.carpeta_sitio}/${each.value}")
  content_type  = lookup(local.tipos_contenido, reverse(split(".", each.value))[0], "application/octet-stream")
  cache_control = "no-cache"
}

resource "aws_s3_object" "config" {
  bucket        = aws_s3_bucket.sitio.id
  key           = "config.js"
  content       = "window.API_URL = \"${local.url_api}\";\n"
  content_type  = "application/javascript; charset=utf-8"
  cache_control = "no-cache"
}

locals {
  url_sitio = (
    local.usa_emulador
    ? "${var.endpoint}/${aws_s3_bucket.sitio.id}/index.html"
    : "http://${aws_s3_bucket_website_configuration.sitio[0].website_endpoint}"
  )
}
