import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega o .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Chave encontrada? {'Sim' if api_key else 'Não'}")

if api_key:
    genai.configure(api_key=api_key)
    print("\n--- TENTANDO LISTAR MODELOS ---")
    try:
        # Tenta listar tudo
        for m in genai.list_models():
            # Filtra apenas os que geram texto
            if 'generateContent' in m.supported_generation_methods:
                print(f"Modelo Disponível: {m.name}")
    except Exception as e:
        print(f"ERRO AO LISTAR: {e}")