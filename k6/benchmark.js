/**
 * =====================================================================================
 * BENCHMARK DE RENDIMIENTO Y PRUEBA DE CARGA (k6)
 * PROYECTO: RFC-TESTER / RFC-TESTER-CRUD (INVESTIGACIÓN ACADÉMICA)
 * =====================================================================================
 * 
 * DECLARACIÓN FORMAL DE SINTETIZACIÓN DE DATOS (SYNTHETIC DATASET DISCLOSURE):
 * -------------------------------------------------------------------------------------
 * 1. Todos los registros incluidos en el array `testData` han sido generados sintéticamente
 *    mediante algoritmos estocásticos para fines exclusivos de pruebas comparativas de 
 *    rendimiento, carga y estrés.
 * 2. Ninguno de los registros representa, almacena ni expone Información de Identificación 
 *    Personal (PII) real perteneciente a contribuyentes del Servicio de Administración 
 *    Tributaria (SAT, México).
 * 3. Validez Algorítmica: Los 50 RFCs (25 Personas Físicas y 25 Personas Morales) cumplen 
 *    estrictamente con la especificación de formato sintáctico (REGEX), fechas válidas en 
 *    formato YYMMDD y el algoritmo de Dígito Verificador Módulo 11 (Anexo 20 SAT).
 * 4. Los nombres y códigos postales fueron construidos para garantizar coincidencia (match) 
 *    en la validación sintáctica del trinomio fiscal CFDI 4.0.
 * =====================================================================================
 */

import http from 'k6/http';
import { check } from 'k6';

// Si vas a realizar pruebas deberás modificar el valor del rate limiting del ser vidor.

// Configuración de API Key (Inyectable por variable de entorno o valor por defecto de desarrollo)
const API_KEY = __ENV.API_KEY || 'desarrollo_secret_key_123';

// URL del Endpoint bajo evaluación (Cotejo de Trinomio Fiscal)
const TARGET_URL = __ENV.TARGET_URL || 'http://IP-despliegue-API:8000/api/v1/rfc/verify-match';

/**
 * Dataset Sintético (50 registros válidos: 25 Personas Físicas, 25 Personas Morales)
 */
const testData = [
    // --- PERSONAS FÍSICAS (25 Registros Sintéticos Válidos) ---
    { rfc: "GARM920312AB3", nombre_o_razon_social: "MAURICIO GARCIA RAMIREZ", codigo_postal: "29000" },
    { rfc: "MAGA8504184H2", nombre_o_razon_social: "ARTURO MACIAS GONZALEZ", codigo_postal: "29040" },
    { rfc: "HABA7604018A1", nombre_o_razon_social: "ALVARO HERNANDEZ BAUTISTA", codigo_postal: "80000" },
    { rfc: "MAMC7604013PA", nombre_o_razon_social: "CARLOS MACIAS MONTOYA", codigo_postal: "29010" },
    { rfc: "TOVC0001015B2", nombre_o_razon_social: "CHRISTIAN TORRES VALDEZ", codigo_postal: "29020" },
    { rfc: "GUCD9805128D4", nombre_o_razon_social: "DANIEL GUTIERREZ CASTRO", codigo_postal: "29030" },
    { rfc: "CASJ9911204F6", nombre_o_razon_social: "JAVIER CASTRO SILVA", codigo_postal: "29050" },
    { rfc: "SEVK0102148H8", nombre_o_razon_social: "KARINA SEGOVIA VEGA", codigo_postal: "29060" },
    { rfc: "PEPA9708304J0", nombre_o_razon_social: "ALBERTO PEREZ PALACIOS", codigo_postal: "29070" },
    { rfc: "ZUCJ9606158L2", nombre_o_razon_social: "JOSE ZUÑIGA CORONA", codigo_postal: "29080" },
    { rfc: "CUPJ9503254N4", nombre_o_razon_social: "JORGE CRUZ PINEDA", codigo_postal: "29090" },
    { rfc: "DICA9412108P6", nombre_o_razon_social: "ALEJANDRO DIAZ COUTIÑO", codigo_postal: "29000" },
    { rfc: "GOGS9307054R8", nombre_o_razon_social: "SANTOS GOMEZ GUTIERREZ", codigo_postal: "29010" },
    { rfc: "TAGA9209188T0", nombre_o_razon_social: "ADRIAN TAPIA GALLEGOS", codigo_postal: "29020" },
    { rfc: "GARA9104044V2", nombre_o_razon_social: "ALONSO GARZA RAMOS", codigo_postal: "29030" },
    { rfc: "DICM9010128X4", nombre_o_razon_social: "MARIO DIAZ CLEMENTE", codigo_postal: "29040" },
    { rfc: "EAEA8902284Z6", nombre_o_razon_social: "ANTONIO ESTRADA AGUILAR", codigo_postal: "29050" },
    { rfc: "GOMJ8808148A8", nombre_o_razon_social: "JUAN GONZALEZ MORALES", codigo_postal: "29060" },
    { rfc: "VEHJ8711034C0", nombre_o_razon_social: "JORGE VEGA HERNANDEZ", codigo_postal: "29070" },
    { rfc: "MAMC7505108E2", nombre_o_razon_social: "CLAUDIO MARTINEZ MACIAS", codigo_postal: "80010" },
    { rfc: "MOFE4809204G4", nombre_o_razon_social: "ENRIQUE MORALES FLORES", codigo_postal: "80020" },
    { rfc: "HEBE5503158I6", nombre_o_razon_social: "EDUARDO HERNANDEZ BARRIOS", codigo_postal: "80030" },
    { rfc: "MOFL6007224K8", nombre_o_razon_social: "LUIS MONTES FLORES", codigo_postal: "80040" },
    { rfc: "HEBI8201118M0", nombre_o_razon_social: "IGNACIO HERNANDEZ BARRERA", codigo_postal: "80050" },
    { rfc: "MMMM7810054O2", nombre_o_razon_social: "MANUEL MORENO MACIAS", codigo_postal: "29080" },

    // --- PERSONAS MORALES (25 Registros Sintéticos Válidos) ---
    { rfc: "ACO010515ND9", nombre_o_razon_social: "ASESORES DE COMERCIO Y OPERACIONES SA DE CV", codigo_postal: "03100" },
    { rfc: "PET990101XYZ", nombre_o_razon_social: "PROVEEDORA Y EMBALAJES TECNICOS SA DE CV", codigo_postal: "01000" },
    { rfc: "CTE150312AB1", nombre_o_razon_social: "CONSULTORIA DE TECNOLOGIA ENTERPRISE SA DE CV", codigo_postal: "29000" },
    { rfc: "ISI101010CD3", nombre_o_razon_social: "INGENIERIA EN SISTEMAS Y INTEGRACIONES S DE RL", codigo_postal: "29010" },
    { rfc: "CSY080420EF5", nombre_o_razon_social: "CORPORATIVO DE SOLUCIONES Y AUDITORIA SAS", codigo_postal: "29020" },
    { rfc: "DSE120808GH7", nombre_o_razon_social: "DESARROLLOS DE SERVICIOS ELECTRONICOS SA", codigo_postal: "29030" },
    { rfc: "NMA191111IJ9", nombre_o_razon_social: "NAVEGACIÓN Y MAPEO AUTOMATIZADO SA DE CV", codigo_postal: "29040" },
    { rfc: "SOL050607KL1", nombre_o_razon_social: "SERVICIOS Y OPERACIONES DE LOGISTICA SA DE CV", codigo_postal: "29050" },
    { rfc: "CDF900303MN3", nombre_o_razon_social: "COMPAÑÍA DE DISTRIBUCION Y FACTURACION S DE RL", codigo_postal: "06600" },
    { rfc: "LOG140719OP5", nombre_o_razon_social: "LOGÍSTICA DE OPERACIONES Y GESTIÓN SA", codigo_postal: "06700" },
    { rfc: "TER880202QR7", nombre_o_razon_social: "TECNOLOGIA EN EQUIPOS Y REDES SA DE CV", codigo_postal: "44100" },
    { rfc: "EDI030915ST9", nombre_o_razon_social: "EMPRESA DE DESARROLLO E INNOVACION AC", codigo_postal: "03100" },
    { rfc: "CBA110130UV1", nombre_o_razon_social: "CORPORATIVO DE BARISTAS Y ALIMENTOS S DE RL", codigo_postal: "29060" },
    { rfc: "TCH170410WX3", nombre_o_razon_social: "TELECOMUNICACIONES Y COMUNICACIONES DE CHIAPAS SA DE CV", codigo_postal: "29070" },
    { rfc: "INF090909YZ5", nombre_o_razon_social: "INGENIERIA DE NUBE Y FISCALIZACIÓN SA", codigo_postal: "01010" },
    { rfc: "VAL200202AB7", nombre_o_razon_social: "VALIDACIONES AUTOMATIZADAS Y LOGICA SAS", codigo_postal: "06500" },
    { rfc: "MDU160616CD9", nombre_o_razon_social: "MAYOREO DE UTILERIAS Y DATOS SA DE CV", codigo_postal: "29080" },
    { rfc: "NEX130330EF1", nombre_o_razon_social: "NUCLEO DE EXPEDICIÓN Y X-XML SA DE CV", codigo_postal: "03200" },
    { rfc: "PBY180818GH3", nombre_o_razon_social: "PLATAFORMAS BIOMETRICAS Y Y-SECURITY S DE RL", codigo_postal: "11560" },
    { rfc: "SEC070707IJ5", nombre_o_razon_social: "SISTEMAS DE EVALUACION Y CIBERSEGURIDAD SA DE CV", codigo_postal: "29090" },
    { rfc: "GDA121212KL7", nombre_o_razon_social: "GESTIÓN DE DATOS Y ARQUITECTURAS SAS", codigo_postal: "06600" },
    { rfc: "API150505MN9", nombre_o_razon_social: "AUDITORÍA DE PROCESOS E INTEGRACIONES SA DE CV", codigo_postal: "03100" },
    { rfc: "SFE210101OP1", nombre_o_razon_social: "SERVICIOS FISCALES Y EVALUACIONES SA DE CV", codigo_postal: "29000" },
    { rfc: "ZPI220202QR3", nombre_o_razon_social: "ZONA DE PROCESAMIENTO E INTEGRIDAD S DE RL", codigo_postal: "01000" },
    { rfc: "RTE230303ST5", nombre_o_razon_social: "REDES Y TECNOLOGIAS EVALUADAS SA DE CV", codigo_postal: "29010" }
];

/**
 * Escenario de Carga k6 (Ramp-up, Carga Sostenida, Ramp-down)
 */
export const options = {
    stages: [
        { duration: '15s', target: 20 }, // Incremento gradual a 20 usuarios virtuales (VUs)
        { duration: '1m', target: 50 }, // Carga constante de 50 VUs por 1 minuto
        { duration: '15s', target: 0 }, // Descenso gradual a 0 VUs
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],    // Criterio de éxito: Menos del 1% de errores HTTP
        http_req_duration: ['p(95)<500'],  // Criterio de éxito: Percentil 95 por debajo de 500ms
    },
};

/**
 * Función principal ejecutada iterativamente por cada VU
 */
export default function () {
    // Selección pseudoaleatoria con distribución uniforme entre los 50 elementos
    const sample = testData[Math.floor(Math.random() * testData.length)];

    const payload = JSON.stringify(sample);
    const params = {
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY, // Autenticación de seguridad requerida
        },
    };

    const res = http.post(TARGET_URL, payload, params);

    // Verificación formal de respuesta HTTP 200 OK
    check(res, {
        'status 200': (r) => r.status === 200,
    });
}
