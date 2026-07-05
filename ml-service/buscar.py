import pandas as pd

# Cambia la ruta si tu CSV está en otra carpeta
ruta = 'F:\main\phiusiil+phishing+url+dataset\PhiUSIIL_Phishing_URL_Dataset.csv' 

print("Cargando el dataset...")
df = pd.read_csv(ruta)

# Filtramos solo los que tienen label == 1 (Phishing) y extraemos la columna URL
urls_maliciosas = df[df['label'] == 1]['URL'].head(5)

print("\n--- 5 URLs de Phishing Confirmadas ---")
for url in urls_maliciosas:
    print(url)