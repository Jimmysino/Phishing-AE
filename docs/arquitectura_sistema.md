# Arquitectura del Sistema: Detección Predictiva de Phishing

## Visión General
Este documento define la arquitectura base para el sistema de detección predictiva y clasificación de sitios web de phishing utilizando algoritmos de Aprendizaje Estadístico[cite: 2]. El sistema migra un modelo de experimentación estructurado (Random Forest optimizado) a una arquitectura de microservicios orientada a la producción para inferencias en tiempo real[cite: 2].

## Componentes del Sistema

### 1. Backend Principal (`backend-core`)
*   **Tecnología:** TypeScript, Nest.js.
*   **Propósito:** Actuar como el orquestador central del sistema. Gestiona la lógica de negocio, procesa las peticiones del cliente (interfaz de usuario o aplicaciones cliente) y maneja la comunicación interna con el microservicio de inteligencia artificial a través de un cliente HTTP dedicado.

### 2. Microservicio de Inferencia (`ml-service`)
*   **Tecnología:** Python, FastAPI, scikit-learn, pandas.
*   **Propósito:** Alojar de forma aislada el modelo predictivo ganador (Random Forest) y ejecutar las inferencias analíticas[cite: 2].
*   **Gestión de Artefactos:** Este servicio requiere la carga en memoria de los archivos físicos (e.g., `.joblib`) correspondientes al modelo Random Forest previamente entrenado y al escalador (`StandardScaler`) ajustado durante la fase de validación cruzada[cite: 1, 2].

## Restricciones Críticas de Pre-procesamiento
Para garantizar la convergencia matemática y evitar la fuga de información (Data Leakage), el flujo de datos hacia el `ml-service` debe cumplir estrictamente con el siguiente pipeline de depuración antes de ejecutar cualquier predicción[cite: 1, 2]:

*   **Eliminación Estricta de Variables:** Es obligatorio excluir deterministamente las columnas `FILENAME`, `URL` y `URLSimilarityIndex` del conjunto de datos de entrada[cite: 1, 2].
*   **Preservación de Nomenclatura:** Las variables numéricas enviadas al modelo deben mantener sus nombres originales de entrenamiento, respetando obligatoriamente las mayúsculas y minúsculas (ej. `HasObfuscation`, `SpacialCharRatioInURL`, `IsHTTPS`).
*   **Estandarización de Datos:** Los datos numéricos de entrada deben ser transformados utilizando el objeto escalador exacto ajustado en la fase de modelado, asegurando que los nuevos vectores entren en la misma distribución espacial que los datos de entrenamiento[cite: 1, 2].