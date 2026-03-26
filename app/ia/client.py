import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
logger = logging.getLogger("gemini_client")

if not api_key:
    logger.warning("GEMINI_API_KEY não encontrada no .env")
else:
    genai.configure(api_key=api_key)

_model = genai.GenerativeModel('gemini-flash-latest')

async def get_gemini_analysis(prompt_text: str):
    try:
        response = await _model.generate_content_async(prompt_text)
        return response.text
    except Exception as e:
        logger.error(f"Erro na comunicação com a IA: {e}")
        return "Não foi possível gerar o relatório no momento. Tente novamente mais tarde."