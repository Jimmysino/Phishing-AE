import json

# 1. Cargamos tu JSON perfecto (que sabemos que tiene exactamente 49 variables)
ruta_base = 'json_perfecto.json'
with open(ruta_base, 'r') as f:
    payload = json.load(f)

features = payload["features"]

# 2. Preparamos nuestra artillería pesada
veneno = {
    "SpacialCharRatioInURL": 0.95,
    "DegitRatioInURL": 0.85,
    "LetterRatioInURL": 0.05,
    "IsDomainIP": 1.0,
    "HasObfuscation": 1.0,
    "ObfuscationRatio": 0.90,
    "NoOfObfuscatedChar": 0.80,
    "HasPasswordField": 1.0,
    "HasHiddenFields": 1.0,
    "HasExternalFormSubmit": 1.0,
    "NoOfPopup": 1.0,
    "NoOfiFrame": 1.0,
    "NoOfIframe": 1.0, # Ponemos ambas por si acaso
    "TLDLegitimateProb": 0.0,
    "URLCharProb": 0.0,
    "DomainTitleMatchScore": 0.0,
    "URLTitleMatchScore": 0.0
}

# 3. LA REGLA DE ORO: Hackeamos de forma segura
# Solo actualizamos el valor si la característica está en las 49 originales
for clave, valor in veneno.items():
    if clave in features:
        features[clave] = valor

# 4. Guardamos el nuevo payload
with open('json_villano.json', 'w') as f:
    json.dump(payload, f, indent=4)

print(f"😈 ¡Malware creado! Total de características: {len(features)}. Ni una más, ni una menos.")