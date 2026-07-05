# Sistema Predictivo de Detección de Phishing 🛡️

## Descripción del Proyecto
Este sistema implementa un motor de Inteligencia Artificial basado en Aprendizaje Estadístico para detectar sitios web de phishing en tiempo real. Utiliza algoritmos de clasificación (Random Forest, Decision Tree, Logistic Regression) para analizar características léxicas y estructurales de URLs.

## Dataset
El modelo fue entrenado utilizando el **PhiUSIIL Phishing URL Dataset**, garantizando una robusta generalización frente a amenazas modernas.

## Rendimiento del Modelo (Random Forest Optimizado)
- **Accuracy:** 99.99%
- **Sensibilidad:** 99.95%

## Arquitectura del Sistema
El proyecto sigue una arquitectura de microservicios:
- `ml-service`: API en FastAPI con el modelo de ML y web scraping.
- `backend-core`: Servidor orquestador en Nest.js.
- `frontend-web`: Interfaz de usuario en React + Vite.

## Instrucciones de Ejecución (Regla de las 3 Terminales)
Para ejecutar el entorno local, abre tres terminales distintas y ejecuta los siguientes comandos en sus respectivos directorios:

1. **Terminal ML (Python):** `cd ml-service` -> `uvicorn main:app --reload`
2. **Terminal Backend (Node):** `cd backend-core` -> `npm run start:dev`
3. **Terminal Frontend (React):** `cd frontend-web` -> `npm run dev`