import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega configurações
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("⚠️ AVISO: GEMINI_API_KEY não encontrada no .env")
else:
    genai.configure(api_key=api_key)

async def get_gemini_analysis(prompt_text: str):
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(prompt_text)
        
        return response.text
    except Exception as e:
        print(f"Erro na comunicação com a inteligencia artificial: {e}")
        return "Não foi possível gerar o relatório no momento. Tente novamente mais tarde."