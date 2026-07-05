import os
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from extractor_url import extract_features

BASE_DIR  = Path(__file__).parent
MODEL_PATH  = BASE_DIR / "artifacts" / "random_forest_optimizado.joblib"
SCALER_PATH = BASE_DIR / "artifacts" / "scaler.joblib"

# Número exacto de features que el modelo espera
EXPECTED_FEATURES = 49

# ── Umbral de decisión ───────────────────────────────────────────────────────
# El modelo fue entrenado con clases balanceadas.  0.5 es el umbral natural.
# Bájalo sólo si quieres más sensibilidad (más falsos positivos a cambio de
# detectar más phishing real).  NO usar valores extremos como 0.15.
DECISION_THRESHOLD = 0.5

rf_model = None
scaler   = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rf_model, scaler
    try:
        rf_model = joblib.load(MODEL_PATH)
        scaler   = joblib.load(SCALER_PATH)
        print("✅ Modelo y scaler cargados correctamente.")
    except FileNotFoundError as e:
        print(f"❌ Artefacto no encontrado: {e}")
    except Exception as e:
        print(f"❌ Error al cargar artefactos: {e}")
    yield


app = FastAPI(
    title="Phishing Detection API",
    description="Microservicio de detección de phishing con Random Forest",
    version="2.1.0",
    lifespan=lifespan,
)


class AnalisisRequest(BaseModel):
    url: str


class AnalisisResponse(BaseModel):
    url_analizada: str
    is_phishing: int          # 0 = legítimo, 1 = phishing
    prob_phishing: float      # probabilidad cruda del modelo [0, 1]
    prob_legitimo: float
    confidence: float         # prob de la clase predicha
    message: str
    features_extracted: int   # número de features generadas (debug)


@app.post("/predict", response_model=AnalisisResponse)
def predecir_phishing(data: AnalisisRequest):
    # ── Validar que los artefactos estén disponibles ─────────────────────────
    if rf_model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="El modelo o el scaler no están disponibles. Revisa los artefactos.",
        )

    # ── 1. Extraer features ──────────────────────────────────────────────────
    try:
        features_dict = extract_features(data.url)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Error al extraer características de la URL: {e}",
        )

    if len(features_dict) != EXPECTED_FEATURES:
        raise HTTPException(
            status_code=500,
            detail=(
                f"El extractor generó {len(features_dict)} features "
                f"en lugar de {EXPECTED_FEATURES}."
            ),
        )

    # Debug: imprime features en consola del servidor
    import json
    print(f"\n🔍 Analizando: {data.url}")
    print(json.dumps(features_dict, indent=2))

    # ── 2. Convertir a array 2D preservando el orden de columnas ─────────────
    # Usamos DataFrame para que el scaler reciba los nombres de columna correctos
    df_input = pd.DataFrame([features_dict])

    # ── 3. Escalar con el mismo StandardScaler del entrenamiento ─────────────
    try:
        X_scaled = scaler.transform(df_input)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al escalar features: {e}",
        )

    # ── 4. Predicción ────────────────────────────────────────────────────────
    try:
        probabilidades  = rf_model.predict_proba(X_scaled)[0]
        prob_legitimo   = float(probabilidades[0])
        prob_phishing   = float(probabilidades[1])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la predicción del modelo: {e}",
        )

    # ── 5. Decisión basada en umbral ─────────────────────────────────────────
    is_phishing = int(prob_phishing >= DECISION_THRESHOLD)
    confidence  = prob_phishing if is_phishing else prob_legitimo

    print(
        f"  → prob_phishing={prob_phishing:.4f} | "
        f"prob_legitimo={prob_legitimo:.4f} | "
        f"resultado={'PHISHING' if is_phishing else 'LEGÍTIMO'}\n"
    )

    return AnalisisResponse(
        url_analizada=data.url,
        is_phishing=is_phishing,
        prob_phishing=round(prob_phishing, 4),
        prob_legitimo=round(prob_legitimo, 4),
        confidence=round(confidence, 4),
        message="Phishing detectado" if is_phishing else "Sitio legítimo",
        features_extracted=len(features_dict),
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": rf_model is not None,
        "scaler_loaded": scaler is not None,
    }
