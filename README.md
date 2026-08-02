# API Verificador y Cotejador de RFC (SAT México)

[![Licencia](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](Dockerfile)
[![OWASP Compliance](https://img.shields.io/badge/Security-OWASP%20API%20Top%2010-red.svg)](https://owasp.org/www-project-api-security/)

Servicio RESTful de alto rendimiento y ciberseguridad para la verificación sintáctica, cálculo del dígito verificador y cotejo de coincidencia de RFCs (Físicos y Morales) con datos fiscales (Trinomio CFDI 4.0: RFC + Nombre + CP).

---

## 🚀 Tabla Comparativa

| Característica | **rfc-tester** | Librerías Regex (`validate-rfc`) | Servicios Web Genéricos |
| :--- | :---: | :---: | :---: |
| **API RESTful Stateless** | ✅ | ❌ | ⚠️ |
| **Documentación Swagger / ReDoc** | ✅ | ❌ | ⚠️ |
| **Validación Sintáctica + Módulo 11 (SAT)** | ✅ | ✅ | ✅ |
| **Cotejo Trinomio CFDI 4.0 (RFC + Nombre + CP)** | ✅ | ❌ | ❌ |
| **Consulta en Vivo SOAP Padrón SAT (`ValidadorRFC`)** | ✅ | ❌ | ⚠️ |
| **Tolerancia a Fallos / Circuit Breaker (`exists_in_sat: null`)** | ✅ | ❌ | ❌ |
| **Zero PII Logging (GDPR / LFPDPPP)** | ✅ | ❌ | ❌ |
| **Protección DDoS / Rate Limiting** | ✅ | ❌ | ❌ |
| **Hardening Docker (Non-root user)** | ✅ | ❌ | ❌ |
| **Encabezados de Seguridad OWASP** | ✅ | ❌ | ❌ |

---

## 💡 Clarificación Arquitectónica: Arquitectura Híbrida de Dos Capas

La API ofrece una **Arquitectura Híbrida Desacoplada** que permite a los sistemas elegir entre máxima velocidad offline o verificación oficial en tiempo real:

1. **Capa 1 - Determinista e In-Memory (`< 5 ms`)** (`POST /api/v1/rfc/validate-syntax` y `/verify-match`):
   - **Procesamiento:** 100% local e instantáneo en memoria RAM.
   - **Mecanismo:** Regex estricto de estructura, algoritmo matemático oficial **Módulo 11** (Anexo 20 del SAT) y cotejo de coincidencia de trinomio fiscal CFDI 4.0.
   - **Dependencias:** Ninguna (procesamiento offline aislado con 100% de disponibilidad).

2. **Capa 2 - Consulta en Vivo SOAP con Resiliencia Controlada** (`POST /api/v1/rfc/verify-sat-live`):
   - **Procesamiento:** Consulta asíncrona en tiempo real al Servicio Web oficial del SAT (`ValidadorRFC.wsdl`).
   - **Connection Pooling (HTTP Keep-Alive):** Reutilización de sockets TLS/SSL con pool de conexiones (`httpx.AsyncClient` singleton) para reducir ~100ms de latencia en peticiones concurrentes.
   - **Sanitización XML & Parseo Defensivo:** Escapado estricto (`html.escape`) para amparar caracteres especiales como `&` en RFCs de personas morales y parseo XML con `xml.etree.ElementTree` con fallback secundario.
   - **Short-Circuit:** Si el RFC es sintácticamente inválido, omite la llamada externa (`sat_service_status: "SKIPPED"`).
   - **Tolerancia a Fallos (Circuit Breaker):** Si los servidores del SAT están caídos o bloqueados, responde sin fallar la API (`HTTP 200`) mediante `exists_in_sat: null` y estado `UNAVAILABLE` / `TIMEOUT`.

---

## 🛡️ Matriz de Amenazas Mitigadas (OWASP API Security Top 10)

| Riesgo OWASP | Mitigación Implementada en `rfc-tester` |
| :--- | :--- |
| **API1:2023 - Broken Object Level Authorization** | Arquitectura 100% *Stateless* (sin IDs de objetos ni persistencia). |
| **API2:2023 - Broken Authentication** | Autenticación basada en API Key obligatoria vía cabecera HTTP (`X-API-Key`). |
| **API4:2023 - Unrestricted Resource Consumption** | *Rate Limiting* (slowapi) de 30 req/min e inyección de límite de payload (Max 10 KB). |
| **API8:2023 - Security Misconfiguration** | Cabeceras de seguridad HTTP (`CSP`, `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`). |
| **API9:2023 - Improper Inventory Management** | Contrato de API OpenAPI 3.0 estricto documentado en `/docs` y `API_CONTRACT.md`. |
| **API10:2023 - Unsafe Consumption of APIs** | Sanitización y normalización Unicode (NFKC) en todas las entradas de texto. |

---

## 🛠️ Requisitos y Despliegue Rápido con Docker

### 1. Clonar y Configurar Entorno
```bash
cp .env.example .env
```

### 2. Iniciar con Docker Compose
```bash
docker compose up --build -d
```

La API quedará escuchando en `http://localhost:8000`.

---

## 📄 Endpoints Implementados y Ejemplos de Consumo

- **Swagger UI (Interactivo):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Contrato de API (Markdown):** Ver archivo [`API_CONTRACT.md`](file:///home/alonso/Proyectos/rfc-tester/API_CONTRACT.md).

### 1. Health Check (Público)
- **Ruta:** `GET /health`
- **Autenticación:** Ninguna
- **Descripción:** Estado de salud del microservicio y métricas básicas para monitorización y balanceadores de carga.
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. Validación Sintáctica Offline (`< 5 ms`)
- **Ruta:** `POST /api/v1/rfc/validate-syntax`
- **Autenticación:** Cabecera `X-API-Key`
- **Descripción:** Evalúa la sintaxis por Regex, calcula el algoritmo **Módulo 11** (Anexo 20 SAT) y extrae metadatos (tipo de persona y fecha estimada).
```bash
curl -X POST "http://localhost:8000/api/v1/rfc/validate-syntax" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: secret-rfc-key-change-me-in-production" \
     -d '{"rfc": "XAXX010101004"}'
```

### 3. Cotejo del Trinomio Fiscal CFDI 4.0 (`< 5 ms`)
- **Ruta:** `POST /api/v1/rfc/verify-match`
- **Autenticación:** Cabecera `X-API-Key`
- **Descripción:** Verifica la estructura del RFC y realiza el cotejo opcional de coincidencia con **Nombre/Razón Social** y **Código Postal** en memoria RAM.
```bash
curl -X POST "http://localhost:8000/api/v1/rfc/verify-match" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: secret-rfc-key-change-me-in-production" \
     -d '{
       "rfc": "XAXX010101004",
       "nombre_o_razon_social": "PUBLICO EN GENERAL",
       "codigo_postal": "01000"
     }'
```

### 4. Consulta en Vivo al Padrón del SAT (SOAP con Resiliencia)
- **Ruta:** `POST /api/v1/rfc/verify-sat-live`
- **Autenticación:** Cabecera `X-API-Key`
- **Descripción:** Consulta asíncrona en tiempo real al Servicio Web del SAT (`ValidadorRFC`). Incluye Short-Circuit local y tolerancia a fallos/bloqueos WAF con `exists_in_sat: null`.
```bash
curl -X POST "http://localhost:8000/api/v1/rfc/verify-sat-live" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: secret-rfc-key-change-me-in-production" \
     -d '{"rfc": "XAXX010101004"}'
```

---

## 👨‍💻 Acerca de y Autoría

- **Autor:** MC. José Alonso Macías Montoya
- **Correo Institucional:** [jmacias@upchiapas.edu.mx](mailto:jmacias@upchiapas.edu.mx)
- **Institución:** Universidad Politécnica de Chiapas

---

## 🔒 Privacidad y Ciberseguridad desde el Diseño (Privacy & Security by Design)

Este proyecto ha sido desarrollado bajo los estándares internacionales de **Privacy by Design (GDPR Art. 25 / ISO 27701)** y **Security by Design (OWASP Top 10)**:

### 1. Privacy by Design (Privacidad desde el Diseño)
- **Arquitectura Stateless (Sin Persistencia):** El procesamiento de RFC, Nombre y Código Postal se realiza únicamente en memoria volátil RAM durante la petición HTTP y se destruye al finalizar. No existen bases de datos ni archivos temporales.
- **Zero PII Logging & Auditoría Enterprise (90 Días de Retención):** Los registros de auditoría se formatean en JSON plano y filtran de forma estricta cualquier dato personal o tributario (sin registrar RFC, Nombre ni Código Postal). Almacenan timestamp ISO 8601, método HTTP, ruta, código de estado, duración en ms, correlation ID (`request_id`) y hashes de IP/User-Agent. Se aplica rotación diaria a medianoche (`midnight`) conservando un historial exacto de 90 días (ISO 27001 A.12.4).
- **Minimización de Datos (Data Minimization):** La API solo solicita los campos estrictamente necesarios para el cotejo fiscal CFDI 4.0.

### 2. Security by Design (Seguridad desde el Diseño)
- **Docker Hardening (CIS Docker Benchmark):** 
  - **Ejecución no-root:** Usuario sin privilegios (`appuser:appgroup`, UID `10001`).
  - **Remoción Total de Capacidades de Kernel:** Declaración `cap_drop: - ALL` para despojar al contenedor de privilegios de kernel innecesarios.
  - **Sistema de Archivos Volátil:** Montaje de `/tmp` en memoria RAM (`tmpfs` 64 MB) con banderas `noexec,nosuid` para evitar la persistencia de temporales.
  - **Salud del Contenedor:** Monitorización automática mediante `healthcheck` nativo de Docker.
  - **Acotación de Recursos (OWASP API4:2023):** Límite de hardware acotado a 1.0 CPU y 512 MB RAM en `docker-compose.yml` (*Nota: Para pruebas de carga masiva o estrés con k6/JMeter, se puede comentar el bloque `deploy:` en `docker-compose.yml`*).
- **Control DDoS y Fuerza Bruta:** Rate Limiting integrado (`slowapi`) con límite de 30 peticiones/minuto por IP/API Key (15/min para consulta SAT Live).
- **Protección de Memoria:** Middleware que limita el tamaño máximo del cuerpo de la petición a 10 KB (`HTTP 413`).
- **Sanitización de Entradas (NFKC):** Normalización de texto para prevenir inyecciones de código, inyección de logs o evasiones Unicode.
- **Cabeceras de Seguridad OWASP:** Inyección automática de `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` y `Content-Security-Policy`.
- **Trazabilidad sin PII:** Inyección automática de la cabecera `X-Request-ID` (Correlation ID) para auditoría de microservicios.

---

## 📄 Licencia

Este proyecto se distribuye bajo la **Licencia MIT**. Es código de **uso libre, abierto y gratuito**.

> **Condición de Uso:** En caso de utilizar, modificar, publicar o redistribuir este código o API en otros proyectos académicos, comerciales o de software libre, se solicita mantener la debida mención o atribución de autoría al **MC. José Alonso Macías Montoya** y a la **Universidad Politécnica de Chiapas**.

---

## ⚖️ Marco Legal y Protección de Datos Personales

1. **Cumplimiento de la LFPDPPP (México):**
   Esta API ha sido diseñada bajo la arquitectura **Stateless (Sin Persistencia)**. Todo el procesamiento de datos personales (RFC, Nombre, Código Postal) se efectúa en memoria volátil únicamente durante la ejecución del ciclo de solicitud/respuesta HTTP. La aplicación **no escribe en bases de datos ni registra en archivos de log ningún dato personal (Zero PII Logging)**.

2. **Responsabilidad del Usuario / Implementador:**
   Cualquier persona física o moral que despliegue, aloje o publique esta API como un servicio hacia terceros (público en general o clientes) asume de forma exclusiva el carácter de **"Responsable del Tratamiento de Datos Personales"** en apego a la **Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP)** y las disposiciones del **INAI**, quedando obligada a publicar su propio **Aviso de Privacidad** y contar con el consentimiento de sus usuarios.

3. **Deslinde de Responsabilidad (Disclaimer):**
   El autor (**MC. José Alonso Macías Montoya**) y la **Universidad Politécnica de Chiapas** quedan completamente liberados de cualquier responsabilidad legal, civil, administrativa, penal o comercial derivada del uso, mal uso, almacenamiento indebido o tratamiento no autorizado de información que realicen terceros utilizando esta herramienta de código abierto.
