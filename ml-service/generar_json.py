import joblib
import json
import os

# 1. Cargamos tu escalador
scaler = joblib.load(os.path.join('artifacts', 'scaler.joblib'))

# 2. Extraemos los nombres exactos que el modelo guardó en su memoria
nombres_variables = scaler.feature_names_in_

# 3. Creamos un diccionario asignándole 0.0 a todas las características
diccionario_prueba = {nombre: 0.0 for nombre in nombres_variables}
payload = {"features": diccionario_prueba}

# 4. Lo guardamos en un archivo de texto
with open('json_perfecto.json', 'w') as f:
    json.dump(payload, f, indent=4)

print(f"¡Éxito! JSON generado. El modelo espera exactamente {len(nombres_variables)} variables.")