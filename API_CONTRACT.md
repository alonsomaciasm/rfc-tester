# Contrato de API: Servicio de Verificación y Cotejo de RFC (SAT México)

**Versión:** 1.0.0  
**Protocolo:** HTTPS / REST  
**Formato de Intercambio:** JSON (`application/json`)  
**Autenticación:** Header HTTP `X-API-Key`

---

## 1. Resumen de Seguridad, Privacidad y Diseño

- **Privacy & Security by Design:** Desarrollado bajo el Reglamento General de Protección de Datos (GDPR Art. 25), ISO 27701 y estándares OWASP.
- **Autenticación Obligatoria:** Todas las peticiones a los endpoints `/api/v1/*` requieren el encabezado HTTP `X-API-Key`.
- **Zero PII Storage:** Esta API opera en modalidad *stateless*. No almacena en base de datos ni escribe en logs ningún dato personal (RFC, Nombres o CPs enviados).
- **Protección Rate Limiting & Payload Limit:** Límite de 30 solicitudes/minuto por IP/Key y cuerpo máximo de 10 KB (`413`).
- **Headers de Ciberseguridad & Trazabilidad:** Implementa directivas de protección OWASP (`nosniff`, `DENY` frames, `CSP`) e inyecta la cabecera `X-Request-ID`.

---

## 2. Autenticación y Encabezados

| Encabezado | Requerido | Valor de Ejemplo | Descripción |
| :--- | :---: | :--- | :--- |
| `Content-Type` | **Sí** | `application/json` | Formato del cuerpo del mensaje |
| `X-API-Key` | **Sí** | `secret-rfc-key-change-me` | Clave de acceso autorizada |

---

## 3. Especificación de Endpoints

### 3.1 Health Check (Estado del Servicio)

- **Ruta:** `GET /health`
- **Autenticación:** Pública (No requiere API Key)
- **Descripción:** Utilizado por balanceadores de carga y herramientas de monitorización.

#### Respuesta de Éxito (`200 OK`)
```json
{
  "status": "healthy",
  "service": "API Verificador de RFC SAT",
  "version": "1.0.0"
}
```

---

### 3.2 Validación Sintáctica de RFC (Offline)

- **Ruta:** `POST /api/v1/rfc/validate-syntax`
- **Autenticación:** Requerida (`X-API-Key`)
- **Descripción:** Verifica la estructura sintáctica por Regex, calcula el dígito verificador (Módulo 11) y extrae metadatos (Tipo de persona y fecha de nacimiento/creación). **100% Offline (Respuesta en <10ms).**

#### Cuerpo de la Solicitud (Request Body)
```json
{
  "rfc": "GOMR920415XYZ"
}
```

#### Respuestas

##### 200 OK (RFC Válido)
```json
{
  "rfc": "GOMR920415XYZ",
  "is_valid_syntax": true,
  "is_checksum_valid": true,
  "person_type": "FISICA",
  "estimated_date": "1992-04-15",
  "is_valid_date": true,
  "status_message": "Estructura y dígito verificador de RFC válidos."
}
```

##### 200 OK (RFC con Dígito Verificador Incorrecto)
```json
{
  "rfc": "GOMR920415AB0",
  "is_valid_syntax": true,
  "is_checksum_valid": false,
  "person_type": "FISICA",
  "estimated_date": "1992-04-15",
  "is_valid_date": true,
  "status_message": "Estructura de RFC válida pero el dígito verificador es incorrecto."
}
```

---

### 3.3 Cotejo de Coincidencia de RFC y Datos Fiscales (Live Match)

- **Ruta:** `POST /api/v1/rfc/verify-match`
- **Autenticación:** Requerida (`X-API-Key`)
- **Descripción:** Verifica la existencia/inscripción del RFC en el SAT y realiza el cotejo opcional de coincidencia con **Nombre/Razón Social** y **Código Postal** (Trinomio CFDI 4.0).

#### Cuerpo de la Solicitud (Request Body)
```json
{
  "rfc": "NSE011210267",
  "nombre_o_razon_social": "NUEVA SOLUCION EMPRESARIAL",
  "codigo_postal": "06700"
}
```
*Nota: `nombre_o_razon_social` y `codigo_postal` son campos opcionales.*

#### Respuestas

##### 200 OK (RFC Válido Estructuralmente y Datos Coinciden)
```json
{
  "rfc": "NSE011210267",
  "is_valid_syntax": true,
  "is_checksum_valid": true,
  "is_structurally_valid": true,
  "match_details": {
    "nombre_matches": true,
    "codigo_postal_matches": true
  },
  "overall_match": true,
  "status_message": "El RFC es válido y todos los datos coinciden con los registros."
}
```

##### 200 OK (RFC Existe pero el Nombre NO Coincide)
```json
{
  "rfc": "NSE011210267",
  "is_valid_syntax": true,
  "is_checksum_valid": true,
  "is_structurally_valid": true,
  "match_details": {
    "nombre_matches": false,
    "codigo_postal_matches": true
  },
  "overall_match": false,
  "status_message": "El RFC es válido pero uno o más datos ingresados no coinciden."
}
```

### 3.4 Consulta en Vivo al Padrón del SAT (Servicio Web SOAP)

- **Ruta:** `POST /api/v1/rfc/verify-sat-live`
- **Autenticación:** Requerida (`X-API-Key`)
- **Rate Limit:** 15 peticiones/minuto
- **Descripción:** Consulta en tiempo real si el RFC se encuentra registrado e inscrito en la base de datos oficial del SAT a través de su servicio web público SOAP (`ValidadorRFC`). Posee tolerancia a fallos (*Fallback controlado* con `exists_in_sat: null`).

#### Cuerpo de la Solicitud (Request Body)
```json
{
  "rfc": "XAXX010101004"
}
```

#### Respuestas

##### 200 OK (RFC Válido y Registrado en el SAT)
```json
{
  "rfc": "XAXX010101004",
  "is_valid_syntax": true,
  "is_checksum_valid": true,
  "is_structurally_valid": true,
  "exists_in_sat": true,
  "sat_service_status": "ONLINE",
  "status_message": "El RFC está registrado y activo en la base de datos del SAT."
}
```

##### 200 OK (Servicio del SAT Fuera de Servicio / Timeout / Fallback)
```json
{
  "rfc": "XAXX010101004",
  "is_valid_syntax": true,
  "is_checksum_valid": true,
  "is_structurally_valid": true,
  "exists_in_sat": null,
  "sat_service_status": "TIMEOUT",
  "status_message": "Tiempo de espera agotado al consultar el servidor del SAT (Timeout)."
}
```

##### 200 OK (RFC Inválido Estructuralmente - Short-Circuit)
```json
{
  "rfc": "INVALIDO123",
  "is_valid_syntax": false,
  "is_checksum_valid": false,
  "is_structurally_valid": false,
  "exists_in_sat": false,
  "sat_service_status": "SKIPPED",
  "status_message": "RFC inválido sintáctica o matemáticamente. Consulta al SAT omitida."
}
```

---

## 4. Códigos de Error Globales

| Código HTTP | Causa | Cuerpo de Respuesta |
| :---: | :--- | :--- |
| `400 Bad Request` | Formato JSON inválido o longitud de RFC/CP fuera de norma. | `{"detail": [{"msg": "El RFC debe tener exactamente 12 o 13 caracteres."}]}` |
| `401 Unauthorized` | Petición sin encabezado `X-API-Key`. | `{"detail": "Falta el encabezado de autenticación requerido 'X-API-Key'"}` |
| `403 Forbidden` | API Key errónea o expirada. | `{"detail": "API Key inválida o no autorizada"}` |
| `429 Too Many Requests` | Exceso de límite de tasa de peticiones. | `{"error": "Rate limit exceeded"}` |

---

## 5. Ejemplos de Consumo

### Ejemplo en cURL
```bash
curl -X POST "http://localhost:8000/api/v1/rfc/verify-match" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: secret-rfc-key-change-me-in-production" \
     -d '{
       "rfc": "NSE011210267",
       "nombre_o_razon_social": "NUEVA SOLUCION EMPRESARIAL",
       "codigo_postal": "06700"
     }'
```

### Ejemplo en Python (`httpx`)
```python
import httpx

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "secret-rfc-key-change-me-in-production"
}

payload = {
    "rfc": "GOMR920415XYZ",
    "nombre_o_razon_social": "RODRIGO GOMEZ MARTINEZ",
    "codigo_postal": "06700"
}

response = httpx.post("http://localhost:8000/api/v1/rfc/verify-match", json=payload, headers=headers)
print(response.json())
```
