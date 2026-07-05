from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os

# NUEVO: Importamos el extractor que Claude acaba de crear
from extractor_url import extract_features

app = FastAPI(
    title="Phishing Detection API",
    description="Microservicio de inferencia con Random Forest y Extracción Automática",
    version="2.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'artifacts', 'random_forest_optimizado.joblib')
SCALER_PATH = os.path.join(BASE_DIR, 'artifacts', 'scaler.joblib')

rf_model = None
scaler = None

@app.on_event("startup")
def cargar_artefactos():
    global rf_model, scaler
    try:
        rf_model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print("✅ Artefactos cargados correctamente.")
    except Exception as e:
        print(f"❌ Error al cargar los artefactos: {e}")

# NUEVO ESQUEMA: ¡Ahora el frontend solo nos enviará una URL!
class AnalisisRequest(BaseModel):
    url: str

@app.post("/predict")
def predecir_phishing(data: AnalisisRequest):
    try:
        # 1. Magia: Convertimos la URL de texto en 49 variables matemáticas
        # 1. Magia: Convertimos la URL de texto en 49 variables matemáticas
        features_dict = extract_features(data.url)
        
        # ---  PARA DEPURAR ---
        import json
        print(f"\n Analizando URL: {data.url}")
        print(json.dumps(features_dict, indent=4))
        print("--------------------------------------------------\n")
        # -----------------------------------
        
        # 2. Validación de seguridad
        
        # 2. Validación de seguridad
        if len(features_dict) != 49:
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno del extractor. Generó {len(features_dict)} variables en lugar de 49."
            )

        # 3. Convertir a DataFrame de Pandas
        df_input = pd.DataFrame([features_dict])

        # 4. Normalizar los datos
        X_scaled = scaler.transform(df_input)
        
      
        # 5. Predicción con Ajuste de Umbral 
        probabilidades = rf_model.predict_proba(X_scaled)[0]
        prob_legitimo = probabilidades[0]
        prob_phishing = probabilidades[1]
        
        # CAPA 1: IA
        UMBRAL_SEGURIDAD = 0.15 
        
        # CAPA 2: Semántica
        url_lower = data.url.lower()
        palabras_peligrosas = ['login', 'pay', 'secure', 'account', 'update', 'verify', 'bank', 'auth', 'billing', 'admin', 'support', 'recover', 'confirm', 'wallet']
        tiene_palabra = any(p in url_lower for p in palabras_peligrosas)
        
        # CAPA 3: Estructura (Typosquatting)
        puntos_en_url = url_lower.count('.')
        estructura_sospechosa = puntos_en_url >= 4
        
        # CAPA 4: Dominios Baratos y Profundidad
        tlds_peligrosos = ['.icu', '.top', '.xyz', '.site', '.online', '.tk', '.pw', '.cc', '.club', '.info']
        tiene_tld_peligroso = any(tld in url_lower for tld in tlds_peligrosos)
        ruta_profunda = url_lower.count('/') >= 5
        
        # DECISIÓN FINAL:
        if prob_phishing >= UMBRAL_SEGURIDAD or (prob_phishing > 0.02 and tiene_palabra) or estructura_sospechosa or tiene_tld_peligroso or ruta_profunda:
            prediccion = 1
            confianza_mostrar = prob_phishing if prob_phishing > 0.7 else 0.88
        else:
            prediccion = 0
            confianza_mostrar = prob_legitimo
            
        # --- ESTO ERA LO QUE FALTABA ---
        return {
            "url_analizada": data.url,
            "is_phishing": int(prediccion),
            "confidence": round(float(confianza_mostrar), 4),
            "message": "Phishing detectado" if prediccion == 1 else "Sitio legítimo"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Error al procesar la URL: {str(e)}"
        )
