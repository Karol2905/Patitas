variable "ambiente" {
  description = "Nombre del ambiente: dev o prod"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.ambiente)
    error_message = "El ambiente debe ser dev o prod."
  }
}

variable "region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "endpoint" {
  description = "URL del emulador (Floci). Vacío para desplegar en AWS real"
  type        = string
  default     = ""
}

variable "retencion_logs_dias" {
  description = "Días que se guardan los logs de la Lambda"
  type        = number
  default     = 14
}

variable "correo_alertas" {
  description = "Correo que recibe las alarmas. Vacío para no crear la suscripción"
  type        = string
  default     = ""
}

variable "concurrencia_maxima" {
  description = "Máximo de ejecuciones simultáneas de la Lambda"
  type        = number
  default     = 10
}
