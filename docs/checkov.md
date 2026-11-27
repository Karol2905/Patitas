# Reglas de Checkov omitidas

Checkov analiza la infraestructura de `infra/` en cada pull request (job **Checkov** de `ci.yml`). Las reglas de esta tabla se omiten en `.checkov.yaml` porque no aplican al MVP o porque su costo no se justifica para una clínica de una sede. Cada una tiene su razón y, cuando corresponde, la fase en la que se retoma.

| Regla | Qué pide | Por qué se omite |
|---|---|---|
| `CKV_AWS_59` | Autorización en los métodos de API Gateway | La agenda es pública y sin cuenta (RF-01). La consulta y la cancelación se protegen con el correo de la cita. El acceso autenticado del personal es la fase 2 (RF-07). |
| `CKV_AWS_76` | Logs de acceso de API Gateway | Los logs de la Lambda en CloudWatch y las trazas de X-Ray cubren RNF-06. Se activan al pasar a AWS real. |
| `CKV2_AWS_4` | Nivel de logs en la etapa de API Gateway | Misma razón que `CKV_AWS_76`. |
| `CKV_AWS_120` | Caché en API Gateway | Las citas cambian en cada reserva y la caché cobra por hora encendida. |
| `CKV2_AWS_29` | WAF delante de API Gateway | El WAF cuesta más que todo el sistema (Sección VIII del HLD). La concurrencia máxima de 10 en la Lambda acota el abuso. Se evalúa en la fase 2 junto con CAPTCHA. |
| `CKV2_AWS_51` | Certificado de cliente en API Gateway | La API la consume el navegador del público, que no tiene certificado de cliente. |
| `CKV2_AWS_53` | Validación de peticiones en API Gateway | La validación está en `backend/validacion.py`, cubierta por pruebas. |
| `CKV_AWS_119` | Cifrado de DynamoDB con una llave KMS propia | La tabla ya tiene cifrado en reposo con la llave de AWS. Una llave propia cuesta USD 1 al mes y no la exige la Ley 1581. |
| `CKV_AWS_158` | Cifrado del grupo de logs con KMS | Los logs solo registran el id de la cita, sin datos personales. |
| `CKV_AWS_173` | Cifrado de las variables de entorno de la Lambda con KMS | La única variable es el nombre de la tabla; no hay secretos. |
| `CKV_AWS_145` | Cifrado de S3 con KMS | El bucket solo guarda los archivos públicos del sitio, ya cifrados con SSE-S3. |
| `CKV_AWS_26` | Cifrado del tema SNS | Las alertas no llevan datos personales. |
| `CKV_AWS_338` | Retención de logs de al menos un año | Se usan 14 días a propósito: menos costo y menos tiempo guardando información (Ley 1581). |
| `CKV_AWS_116` | Cola de mensajes fallidos en la Lambda | Solo aplica a invocaciones asíncronas; API Gateway invoca la Lambda de forma síncrona y el cliente recibe el error. |
| `CKV_AWS_117` | Lambda dentro de una VPC | La Lambda no accede a recursos privados. Una VPC agrega un NAT Gateway (costo fijo) y arranques en frío más lentos. |
| `CKV_AWS_272` | Firma de código de la Lambda | Solo el pipeline despliega, después de pruebas, rulesets y la aprobación del ambiente `prod`. |
| `CKV_AWS_54` | Bloquear políticas públicas en S3 | En el MVP el sitio se sirve desde el endpoint público de S3. En la fase 2 el bucket pasa a privado detrás de CloudFront. |
| `CKV_AWS_56` | Restringir buckets públicos en S3 | Misma razón que `CKV_AWS_54`. |
| `CKV2_AWS_6` | Bloqueo de acceso público en S3 | Misma razón que `CKV_AWS_54`. |
| `CKV_AWS_18` | Logs de acceso de S3 | Es un sitio estático. En la fase 2 se usan los logs de CloudFront. |
| `CKV2_AWS_61` | Reglas de ciclo de vida en S3 | El bucket guarda unos 265 KB de archivos que Terraform reemplaza en cada despliegue. |
| `CKV2_AWS_62` | Notificaciones de eventos de S3 | Ningún proceso reacciona a cambios del bucket. |
| `CKV_AWS_144` | Replicación de S3 a otra región | El sitio se reconstruye desde el repositorio con Terraform, dentro del RTO de 4 h (RNF-04). |
